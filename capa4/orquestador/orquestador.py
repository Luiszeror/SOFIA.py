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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.evaluador import EvaluadorPython, CasoPrueba
from casos_de_prueba.repositorio import obtener_casos
from capa2.retriever.retriever_rag import RetrieverRAG
from capa4.agentes.agente_tutor import AgenteTutor
from capa4.agentes.agente_analista import AgenteAnalista
from capa4.agentes.agente_generador import AgenteGenerador
from error_community.api.community_service import CommunityService

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
        semestre: int = 1,
        enunciado_ejercicio: dict = None,
        preguntas_sin_codigo: int = 0,
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
        # Capturar stdout del sandbox para mostrarlo en la interfaz
        stdout_codigo = ""
        if resultado_eval.resultados_casos:
            stdout_codigo = resultado_eval.resultados_casos[0].salida_obtenida or ""
        elif resultado_eval.metadata.get("stdout"):
            stdout_codigo = resultado_eval.metadata["stdout"]

        # ── PASO 2: Capa 2 — Recuperar contexto RAG ──────────────────────
        resultado_rag = self.retriever.recuperar(
            query                = codigo,
            concepto_hint        = concepto,
            filtrar_por_concepto = True,
        )

        # ── PASO 3: Agente Analista — Actualizar perfil ───────────────────
        perfil = self.analista.cargar_perfil(estudiante_id, nombre_estudiante, semestre)
        resuelto = resultado_eval.tipo_error.value == "correcto"
        perfil = self.analista.actualizar_tras_interaccion(
            perfil    = perfil,
            concepto  = concepto,
            tipo_error = resultado_eval.tipo_error.value,
            intento   = intento,
            resuelto  = resuelto,
        )

        # ── Paso del grafo ─────────────────────────────────────
        comunidad = self._consultar_grafo(
            estudiante_id=estudiante_id,
            tipo_error=diagnostico["tipo_error"],
            concepto=diagnostico["concepto"],
            perfil=perfil  # objeto con .score_riesgo, .errores_por_concepto etc.
        )

        # ── PASO 4: Agente Tutor — Respuesta socrática ───────────────────
        if self._llm_disponible:
            try:
                resumen_perfil = self.analista.generar_resumen_para_tutor(perfil)
                perfil_para_tutor = {
                    **perfil.to_dict(),
                    "resumen": resumen_perfil,
                }
                resp_tutor = self.tutor.responder(
                    codigo               = codigo,
                    resultado_capa3      = resultado_dict,
                    resultado_capa2      = resultado_rag,
                    perfil               = perfil_para_tutor,
                    intento              = intento,
                    historial            = historial or [],
                    enunciado_ejercicio  = enunciado_ejercicio,
                    preguntas_sin_codigo = preguntas_sin_codigo,
                )
                respuesta_texto = resp_tutor["respuesta"]
                fuentes         = resp_tutor["fuentes"]
            except Exception as e:
                print(f"  [Orquestador] LLM no disponible: {type(e).__name__} — modo básico")
                respuesta_texto = resultado_eval.sugerencia_socratica
                if resultado_rag.fragmentos:
                    frag = resultado_rag.fragmentos[0]
                    respuesta_texto += f"\n\n📖 Del material del curso ({frag.capitulo}): recuerda revisar este concepto."
                fuentes = resultado_rag.fuentes
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
            "stdout_codigo":    stdout_codigo,
            "consola_output":   resultado_dict.get("consola_output", ""),
            "comunidad": comunidad,
        }

    def responder_pregunta(
        self,
        pregunta: str,
        concepto_hint: str = "general",
        estudiante_id: str = "estudiante",
        nombre_estudiante: str = "Estudiante",
        historial: list = None,
        semestre: int = 1,
        preguntas_sin_codigo: int = 0,
        enunciado_ejercicio: dict = None,
    ) -> dict:
        """
        Responde preguntas conceptuales del estudiante.
        Usa el RAG para anclar la respuesta al material del curso.
        El tutor responde de forma socrática — con otra pregunta al final.
        """
        if historial is None:
            historial = []

        # RAG — buscar contexto relevante
        # Buscar primero por concepto_hint (filtro directo por categoría)
        # Si no hay resultados, buscar sin filtro
        resultado_rag = self.retriever.recuperar(
            query                = pregunta,
            concepto_hint        = concepto_hint,
            filtrar_por_concepto = True,   # busca solo en chunks de ese concepto
        )
        # Si no encontró nada en el concepto, buscar en todo el corpus
        if not resultado_rag.fragmentos:
            resultado_rag = self.retriever.recuperar(
                query         = pregunta,
                concepto_hint = concepto_hint,
            )

        # Extraer fragmento del corpus SIEMPRE (antes del LLM)
        fragmento_corpus = ""
        if resultado_rag.fragmentos:
            frag = resultado_rag.fragmentos[0]
            texto_limpio = frag.texto.replace("\n", " ").strip()
            fragmento_corpus = texto_limpio[:500] + ("..." if len(texto_limpio) > 500 else "")

        if self._llm_disponible:
            try:
                resultado_capa3_simulado = {
                    "tipo_error":       "pregunta_conceptual",
                    "concepto":         concepto_hint,
                    "mensaje_tecnico":  pregunta,
                    "linea_error":      None,
                    "casos_pasados":    0,
                    "casos_ejecutados": 0,
                }
                perfil = self.analista.cargar_perfil(estudiante_id, nombre_estudiante, semestre)
                resp = self.tutor.responder(
                    codigo          = f"# Pregunta del estudiante: {pregunta}",
                    resultado_capa3 = resultado_capa3_simulado,
                    resultado_capa2 = resultado_rag,
                    perfil          = perfil.to_dict(),
                    intento         = 1,
                    historial       = historial,
                )
                return {
                    "respuesta":        resp["respuesta"],
                    "fuentes":          resp["fuentes"],
                    "fragmento_corpus": fragmento_corpus,
                    "fragmentos":       [{"texto": f.texto, "capitulo": f.capitulo}
                                         for f in resultado_rag.fragmentos],
                }
            except Exception as e:
                print(f"  [Orquestador] LLM no disponible: {type(e).__name__} — usando fallback")

        # Fallback — respuesta básica sin LLM
        if resultado_rag.fragmentos:
            frag = resultado_rag.fragmentos[0]
            oraciones = [s.strip() for s in frag.texto.replace("\n"," ").split(".") if len(s.strip()) > 20][:3]
            extracto  = ". ".join(oraciones) + "." if oraciones else frag.texto[:300]
            respuesta = (
                f"Del material del curso ({frag.capitulo}):\n\n"
                f"{extracto}\n\n"
                f"¿Qué parte de esto te genera más dudas?"
            )
        else:
            # Buscar sin filtro de concepto como último recurso
            rag_sin_filtro = self.retriever.recuperar(query=pregunta, concepto_hint="general")
            if rag_sin_filtro.fragmentos:
                frag = rag_sin_filtro.fragmentos[0]
                oraciones = [s.strip() for s in frag.texto.replace("\n"," ").split(".") if len(s.strip()) > 20][:2]
                extracto  = ". ".join(oraciones) + "."
                respuesta = (
                    f"Del material del curso ({frag.capitulo}):\n\n"
                    f"{extracto}\n\n"
                    f"¿Qué parte te genera más dudas?"
                )
            else:
                # Detectar si la pregunta es sobre otro lenguaje
                otros_lenguajes = ["java", "javascript", "c++", "c#", "php", "ruby",
                                   "swift", "kotlin", "syso", "system.out", "console.log",
                                   "printf", "cout", "println"]
                pregunta_lower = pregunta.lower()
                if any(lang in pregunta_lower for lang in otros_lenguajes):
                    respuesta = ("Este curso se enfoca en Python. "
                                 "Lo que preguntas parece ser de otro lenguaje. "
                                 "¿Te gustaría explorar el concepto equivalente en Python?")
                else:
                    respuesta = "No encontré ese tema en el material del curso. ¿Puedes ser más específico sobre qué parte de Python quieres explorar?"

        return {
            "respuesta":        respuesta,
            "fuentes":          resultado_rag.fuentes,
            "fragmento_corpus": fragmento_corpus,
            "fragmentos":       [{"texto": f.texto, "capitulo": f.capitulo}
                                 for f in resultado_rag.fragmentos],
        }

    def evaluar_respuesta_estudiante(
        self,
        respuesta_estudiante: str,
        pregunta_sofia: str,
        concepto: str,
        estudiante_id: str,
        nombre_estudiante: str = "Estudiante",
        historial: list = None,
    ) -> dict:
        """
        Evalúa si la respuesta del estudiante a una pregunta socrática es correcta.
        Si es correcta, reduce el score de riesgo.
        """
        if historial is None:
            historial = []

        resultado_rag = self.retriever.recuperar(
            query         = pregunta_sofia,
            concepto_hint = concepto,
        )

        if self._llm_disponible:
            try:
                prompt_eval = {
                    "tipo_error":       "respuesta_estudiante",
                    "concepto":         concepto,
                    "mensaje_tecnico":  f"Pregunta de SOFIA: {pregunta_sofia}\nRespuesta del estudiante: {respuesta_estudiante}",
                    "linea_error":      None,
                    "casos_pasados":    0,
                    "casos_ejecutados": 0,
                }
                perfil = self.analista.cargar_perfil(estudiante_id, nombre_estudiante, semestre)
                resp   = self.tutor.responder(
                    codigo          = f"# Respuesta del estudiante: {respuesta_estudiante}",
                    resultado_capa3 = prompt_eval,
                    resultado_capa2 = resultado_rag,
                    perfil          = perfil.to_dict(),
                    intento         = 1,
                    historial       = historial,
                )
                # Si la respuesta fue correcta, bajar el score
                texto = resp["respuesta"].lower()
                fue_correcto = any(p in texto for p in [
                    "correcto", "exacto", "excelente", "muy bien", "perfecto",
                    "así es", "en efecto", "tienes razón", "acertaste"
                ])
                if fue_correcto:
                    self.analista.registrar_respuesta_correcta(perfil, concepto)

                return {
                    "respuesta":     resp["respuesta"],
                    "fuentes":       resp["fuentes"],
                    "fue_correcto":  fue_correcto,
                }
            except Exception as e:
                print(f"  [Orquestador] Error LLM evaluar respuesta: {e}")

        return {
            "respuesta":    "Interesante respuesta. ¿Puedes elaborar un poco más?",
            "fuentes":      [],
            "fue_correcto": False,
        }

    def _consultar_grafo(self, estudiante_id: str, tipo_error: str,
                         concepto: str, perfil) -> dict:
        """
        Traduce los datos de SOFIA.py al formato del grafo y
        consulta CommunityService. Si falla, retorna dict vacío
        para no interrumpir la sesión del estudiante.
        """

        # Mapeo directo desde los 5 tipos de evaluador.py
        severidad_map = {
            "error_sintaxis": 1,
            "error_logico": 2,
            "error_runtime": 3,
            "error_timeout": 3,
            "error_seguridad": 4,
            "correcto": 0,
        }

        # Mapeo desde los 9 conceptos del repositorio de casos
        concepto_map = {
            "variables": 0,
            "funciones": 1,
            "condicionales": 2,
            "ciclos": 3,
            "listas": 4,
            "diccionarios": 5,
            "clases": 6,
            "recursion": 7,
            "strings": 8,
        }

        try:
            # Construir datos desde el perfil real de SOFIA.py
            # perfil es un objeto con atributos (no un dict)
            estudiante_data = {
                "id": estudiante_id,
                "total_attempts": getattr(perfil, "interacciones", 1),
                "error_rate": min(getattr(perfil, "score_riesgo", 0) / 10.0, 1.0),
                "avg_time_sec": getattr(perfil, "intentos_promedio", 1) * 60,
            }

            error_data = {
                "type_id": concepto_map.get(concepto, 0),
                "frequency": getattr(perfil, "errores_por_concepto", {}).get(concepto, 1),
                "severity": severidad_map.get(tipo_error, 2),
                "module_id": concepto_map.get(concepto, 0),
            }

            concept_data = {
                "concept_id": concepto_map.get(concepto, 0),
                "semester": 1,
                "difficulty": 0.7,
            }

            # Mapa de errores por estudiante para label_communities
            student_error_map = {
                estudiante_id: getattr(perfil, "errores_frecuentes", [tipo_error])
            }

            self._community_service.run_pipeline(
                students=[estudiante_data],
                errors=[error_data],
                concepts=[concept_data],
                student_commits_error=[(0, 0)],
                student_studies_concept=[(0, 0)],
                error_maps_concept=[(0, 0)],
                student_error_map=student_error_map,
            )

            return self._community_service.get_community_for_student(estudiante_id)

        except Exception as e:
            # Modo degradado: el tutor sigue funcionando sin el grafo
            print(f"[GRL-DCE] Advertencia: {e}")
            return {
                "community": None,
                "dominant_errors": [tipo_error],
                "risk_level": "unknown",
                "size": 1,
            }

