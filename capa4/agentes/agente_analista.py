"""
AGENTE 2 — Analista de Aprendizaje
Capa 4 — Sistema de Tutoría Socrática UPTC

Trabaja en segundo plano. El estudiante nunca lo ve.
Construye y actualiza el perfil de cada estudiante.
Calcula score de riesgo y activa alertas para el docente.
"""

import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict

UMBRAL_RIESGO = 6.5  # score sobre 10 que activa alerta


@dataclass
class PerfilEstudiante:
    estudiante_id:     str
    nombre:            str = "Estudiante"
    semestre:          int = 1
    sesiones:          int = 0
    interacciones:     int = 0
    errores_por_concepto: dict = field(default_factory=dict)
    intentos_por_concepto: dict = field(default_factory=dict)
    errores_frecuentes: list = field(default_factory=list)
    intentos_promedio:  float = 0.0
    score_riesgo:       float = 0.0
    en_alerta:          bool = False
    ultima_sesion:      str = ""
    historial_errores:  list = field(default_factory=list)  # últimos 20

    def to_dict(self) -> dict:
        return asdict(self)


class AgenteAnalista:
    """
    Agente 2 — Analista de Aprendizaje.
    Mantiene perfiles persistentes en JSON por estudiante.
    """

    def __init__(self, directorio_perfiles: str = "data/perfiles"):
        self.directorio = Path(directorio_perfiles)
        self.directorio.mkdir(parents=True, exist_ok=True)

    def _ruta_perfil(self, estudiante_id: str) -> Path:
        return self.directorio / f"{estudiante_id}.json"

    def cargar_perfil(self, estudiante_id: str, nombre: str = "Estudiante", semestre: int = 1) -> PerfilEstudiante:
        ruta = self._ruta_perfil(estudiante_id)
        if ruta.exists():
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("semestre", semestre)
            return PerfilEstudiante(**data)
        return PerfilEstudiante(estudiante_id=estudiante_id, nombre=nombre, semestre=semestre)

    def guardar_perfil(self, perfil: PerfilEstudiante):
        ruta = self._ruta_perfil(perfil.estudiante_id)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(perfil.to_dict(), f, ensure_ascii=False, indent=2)

    def actualizar_tras_interaccion(
        self,
        perfil: PerfilEstudiante,
        concepto: str,
        tipo_error: str,
        intento: int,
        resuelto: bool,
    ) -> PerfilEstudiante:
        """
        Actualiza el perfil después de cada interacción del estudiante.
        Recalcula score de riesgo y determina si debe activarse alerta.
        """
        perfil.interacciones += 1
        perfil.ultima_sesion = time.strftime("%Y-%m-%d %H:%M")

        # Registrar error por concepto
        if tipo_error not in ("correcto",):
            perfil.errores_por_concepto[concepto] = (
                perfil.errores_por_concepto.get(concepto, 0) + 1
            )
            perfil.historial_errores.append({
                "concepto":   concepto,
                "tipo_error": tipo_error,
                "intento":    intento,
                "timestamp":  perfil.ultima_sesion,
            })
            # Mantener solo los últimos 20
            perfil.historial_errores = perfil.historial_errores[-20:]

        # Registrar intentos por concepto
        if concepto not in perfil.intentos_por_concepto:
            perfil.intentos_por_concepto[concepto] = []
        perfil.intentos_por_concepto[concepto].append(intento)

        # Calcular intentos promedio global
        todos_intentos = [
            i for lista in perfil.intentos_por_concepto.values() for i in lista
        ]
        perfil.intentos_promedio = round(
            sum(todos_intentos) / max(len(todos_intentos), 1), 1
        )

        # Top 3 conceptos con más errores
        if perfil.errores_por_concepto:
            perfil.errores_frecuentes = sorted(
                perfil.errores_por_concepto,
                key=perfil.errores_por_concepto.get,
                reverse=True,
            )[:3]

        # Score de riesgo (0-10)
        factor_intentos    = min(perfil.intentos_promedio / 5 * 4, 4)
        factor_errores     = min(sum(perfil.errores_por_concepto.values()) / 10 * 3, 3)
        factor_no_resuelve = 3 if (intento >= 5 and not resuelto) else 0
        # Factor positivo: si resuelve, reduce el score
        factor_positivo    = -1.5 if resuelto else 0
        perfil.score_riesgo = max(0, round(factor_intentos + factor_errores + factor_no_resuelve + factor_positivo, 1))
        perfil.en_alerta = perfil.score_riesgo >= UMBRAL_RIESGO

        self.guardar_perfil(perfil)
        return perfil

    def generar_resumen_para_tutor(self, perfil: PerfilEstudiante) -> str:
        """
        Genera un resumen conciso del perfil para incluir en el contexto del Agente Tutor.
        """
        if perfil.interacciones == 0:
            return "Primera interacción del estudiante con el sistema."

        partes = []
        if perfil.errores_frecuentes:
            partes.append(
                f"Dificultades recurrentes en: {', '.join(perfil.errores_frecuentes)}."
            )
        if perfil.intentos_promedio > 3:
            partes.append(
                f"Necesita en promedio {perfil.intentos_promedio} intentos por ejercicio."
            )
        if perfil.en_alerta:
            partes.append("ALERTA: estudiante con alto riesgo de abandono.")

        return " ".join(partes) if partes else "Estudiante con buen desempeño general."


    def registrar_respuesta_correcta(self, perfil, concepto: str) -> "PerfilEstudiante":
        """
        Registra que el estudiante respondió correctamente una pregunta socrática.
        Reduce el score de riesgo.
        """
        perfil.score_riesgo = max(0, round(perfil.score_riesgo - 0.5, 1))
        perfil.en_alerta    = perfil.score_riesgo >= UMBRAL_RIESGO
        self.guardar_perfil(perfil)
        return perfil

    def listar_estudiantes_en_alerta(self) -> list[dict]:
        """Retorna lista de estudiantes que superaron el umbral de riesgo."""
        alertas = []
        for archivo in self.directorio.glob("*.json"):
            with open(archivo, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("en_alerta"):
                alertas.append(data)
        return alertas
