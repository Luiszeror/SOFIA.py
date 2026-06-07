"""
ORQUESTADOR — Capa 4
Sistema de Tutoría Socrática UPTC

Coordina los 3 agentes en respuesta a cada interacción del estudiante.
Conecta Capa 3 (evaluador) + Capa 2 (RAG) + Agentes 1, 2 y 3.

Flujo por interacción:
  1. Capa 3 evalúa el código
  2. Capa 2 recupera contexto del libro
  3. Agente Analista actualiza el perfil
  4. Agente Tutor genera la respuesta socrática
  5. Si score_riesgo alto → Agente Generador propone ejercicio nuevo
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from core.evaluador import EvaluadorPython, CasoPrueba
from casos_de_prueba.repositorio import obtener_casos
from capa2.retriever.retriever_rag import RetrieverRAG
from capa4.agentes.agente_tutor import AgenteTutor
from capa4.agentes.agente_analista import AgenteAnalista
from capa4.agentes.agente_generador import AgenteGenerador


class Orquestador:
    """
    Punto de entrada principal del sistema completo.
    La interfaz (Capa 1 / app.py) solo habla con este orquestador.
    """

    def __init__(self, directorio_db: str = "data/chroma_db"):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        self.evaluador  = EvaluadorPython(timeout_seg=5)
        self.retriever  = RetrieverRAG(
            directorio_db=os.path.join(raiz, directorio_db),
            top_k=3, score_minimo=0.1,
        )
        self.analista   = AgenteAnalista(
            directorio_perfiles=os.path.join(raiz, "data", "perfiles")
        )
        self.generador  = AgenteGenerador()

        try:
            self.tutor = AgenteTutor()
            self._llm_disponible = True
        except ValueError:
            self.tutor = None
            self._llm_disponible = False
            print("  [Orquestador] Sin GROQ_API_KEY — modo básico")

    def procesar(
        self,
        codigo: str,
        concepto: str,
        estudiante_id: str,
        nombre_estudiante: str = "Estudiante",
        intento: int = 1,
        historial: list = None,
        modo_libre: bool = False,
    ) -> dict:
        """
        Pipeline completo por cada interacción del estudiante.

        Retorna dict con todo lo necesario para la interfaz:
        {
            "respuesta_tutor":  str,
            "tipo_error":       str,
            "concepto":         str,
            "casos_pasados":    int,
            "casos_total":      int,
            "fuentes":          list[str],
            "perfil":           dict,
            "ejercicio_nuevo":  dict | None,
            "en_alerta":        bool,
            "llm_activo":       bool,
        }
        """
        if historial is None:
            historial = []

        # ── PASO 1: Capa 3 — Evaluar código ──────────────────────────────
        if modo_libre:
            resultado_eval = self.evaluador.evaluar_libre(codigo, concepto, intento)
        else:
            casos = obtener_casos(concepto)
            if not casos:
                casos = [CasoPrueba("ejecución libre", None, "", concepto)]
            resultado_eval = self.evaluador.evaluar(codigo, casos, concepto, intento)
        resultado_dict = resultado_eval.to_dict()

        # ── PASO 2: Capa 2 — Recuperar contexto RAG ──────────────────────
        resultado_rag = self.retriever.recuperar(
            query                = codigo,
            concepto_hint        = concepto,
            filtrar_por_concepto = True,
        )

        # ── PASO 3: Agente Analista — Actualizar perfil ───────────────────
        perfil = self.analista.cargar_perfil(estudiante_id, nombre_estudiante)
        resuelto = resultado_eval.tipo_error.value == "correcto"
        perfil = self.analista.actualizar_tras_interaccion(
            perfil    = perfil,
            concepto  = concepto,
            tipo_error = resultado_eval.tipo_error.value,
            intento   = intento,
            resuelto  = resuelto,
        )

        # ── PASO 4: Agente Tutor — Respuesta socrática ───────────────────
        if self._llm_disponible:
            resumen_perfil = self.analista.generar_resumen_para_tutor(perfil)
            perfil_para_tutor = {
                **perfil.to_dict(),
                "resumen": resumen_perfil,
            }
            resp_tutor = self.tutor.responder(
                codigo          = codigo,
                resultado_capa3 = resultado_dict,
                resultado_capa2 = resultado_rag,
                perfil          = perfil_para_tutor,
                intento         = intento,
                historial       = historial,
            )
            respuesta_texto = resp_tutor["respuesta"]
            fuentes         = resp_tutor["fuentes"]
        else:
            # Sin LLM: usar sugerencia del evaluador + fragmento del RAG
            respuesta_texto = resultado_eval.sugerencia_socratica
            if resultado_rag.fragmentos:
                frag = resultado_rag.fragmentos[0]
                respuesta_texto += f"\n\n📖 Del material del curso ({frag.capitulo}): recuerda revisar este concepto."
            fuentes = resultado_rag.fuentes

        # ── PASO 5: Agente Generador — Ejercicio nuevo si hay laguna ─────
        ejercicio_nuevo = None
        if perfil.score_riesgo >= 4.0 and concepto in perfil.errores_por_concepto:
            errores_en_concepto = perfil.errores_por_concepto.get(concepto, 0)
            if errores_en_concepto >= 2:
                ejercicio_nuevo = self.generador.generar_ejercicio(
                    concepto        = concepto,
                    dificultad      = "basico",
                    errores_previos = perfil.errores_frecuentes,
                )

        return {
            "respuesta_tutor":  respuesta_texto,
            "tipo_error":       resultado_eval.tipo_error.value,
            "concepto":         concepto,
            "casos_pasados":    resultado_eval.casos_pasados,
            "casos_total":      resultado_eval.casos_ejecutados,
            "mensaje_tecnico":  resultado_eval.mensaje_tecnico,
            "linea_error":      resultado_eval.linea_error,
            "fuentes":          fuentes,
            "perfil":           perfil.to_dict(),
            "ejercicio_nuevo":  ejercicio_nuevo,
            "en_alerta":        perfil.en_alerta,
            "llm_activo":       self._llm_disponible,
            "tiempo_ms":        resultado_rag.tiempo_ms,
        }
