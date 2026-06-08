"""
AGENTE 1 — Tutor Socrático
Capa 4 — Sistema de Tutoría Socrática UPTC

LLM: Google Gemini (cuando hay créditos) o modo básico.
"""

import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT_SOCRATICO = """Eres SOFIA, un tutor socrático de Python. Respondes SIEMPRE en español.
Tienes acceso al historial completo de la conversación — ÚSALO SIEMPRE para dar continuidad.

REGLAS ABSOLUTAS:
1. NUNCA escribas código corregido completo.
2. NUNCA des la respuesta directamente.
3. SIEMPRE termina con exactamente UNA pregunta socrática.
4. Usa el material del curso (=== MATERIAL ===) para anclar tus respuestas.
5. Sé cálido y específico. Máximo 4 oraciones + la pregunta final.
6. NUNCA ignores el historial — si el estudiante ya preguntó sobre el tema, no repitas la explicación básica.

FLUJO PROGRESIVO SEGÚN PREGUNTAS CONSECUTIVAS SIN CÓDIGO:
- Pregunta 1: Explicar el concepto con material del corpus. Terminar con pregunta amplia.
- Pregunta 2: Dar pista más concreta usando lo que dijo antes. Mencionar el ejercicio pendiente.
- Pregunta 3+: Casi revelar la solución en forma de pregunta. Invitar a escribir código.

CUANDO HAY CÓDIGO CON ERROR:
- Mencionar EXPLÍCITAMENTE qué pide el ejercicio y cómo difiere de lo que hizo el estudiante.
- Conectar con lo conversado antes si aplica.
- Señalar la línea específica del código que causa el problema.
- Terminar con pregunta sobre ESA línea específica.

CUANDO EL CÓDIGO ES CORRECTO:
- Felicitar genuinamente y conectar con el proceso.
- Hacer pregunta de consolidación sobre el concepto.

FLUJO DE EVALUACIÓN CONJUNTA:
- SIEMPRE referenciar la conversación previa: "Recuerda que hablamos de...".
- Guiar paso a paso hacia la corrección con preguntas cada vez más específicas."""


def construir_prompt(codigo, resultado_capa3, contexto_rag, perfil, intento,
                     historial, enunciado_ejercicio=None, preguntas_sin_codigo=0):

    perfil_texto = ""
    if perfil.get("errores_frecuentes"):
        errores = ", ".join(perfil["errores_frecuentes"][:3])
        perfil_texto = (
            f"\n[Perfil del estudiante]\n"
            f"Errores frecuentes en: {errores}\n"
            f"Score de riesgo: {perfil.get('score_riesgo', 0):.1f}/10\n"
        )

    tipo_error    = resultado_capa3.get("tipo_error", "general")
    concepto      = resultado_capa3.get("concepto", "general")
    msg_tecnico   = resultado_capa3.get("mensaje_tecnico", "")
    linea_error   = resultado_capa3.get("linea_error")
    casos_pasados = resultado_capa3.get("casos_pasados", 0)
    casos_total   = resultado_capa3.get("casos_ejecutados", 0)

    diagnostico = (
        f"\n[Diagnóstico del evaluador]\n"
        f"Tipo de error: {tipo_error}\n"
        f"Concepto: {concepto}\n"
        f"Mensaje técnico: {msg_tecnico}\n"
        + (f"Línea del error: {linea_error}\n" if linea_error else "")
        + f"Casos de prueba: {casos_pasados}/{casos_total} correctos\n"
        f"Intento número: {intento}\n"
    )

    ejercicio_txt = ""
    if enunciado_ejercicio:
        ejercicio_txt = (
            f"\n[Ejercicio actual del estudiante]\n"
            f"Nombre: {enunciado_ejercicio.get('nombre', '')}\n"
            f"Enunciado: {enunciado_ejercicio.get('descripcion', '')}\n"
            f"Salida esperada: {enunciado_ejercicio.get('salida_esperada', '')}\n"
            f"Conecta el error con este ejercicio específico.\n"
        )

    if preguntas_sin_codigo == 0:
        modo_txt = "[Modo: evaluación de código — conectar con conversación previa]"
    elif preguntas_sin_codigo == 1:
        modo_txt = "[Modo: primera pregunta — explicar con corpus, pregunta amplia]"
    elif preguntas_sin_codigo == 2:
        modo_txt = "[Modo: segunda pregunta — pista concreta, mencionar ejercicio]"
    else:
        modo_txt = "[Modo: tercera+ pregunta — casi revelar solución, invitar a escribir código]"

    historial_texto = ""
    if historial:
        historial_texto = "\n[Historial de la sesión]\n"
        for msg in historial[-12:]:
            rol = "Estudiante" if msg["role"] == "user" else "SOFIA"
            contenido = msg["content"][:300].replace("```python", "[código]").replace("```", "")
            historial_texto += f"{rol}: {contenido}\n"

    return (
        f"{SYSTEM_PROMPT_SOCRATICO}\n\n"
        f"{modo_txt}\n"
        f"{perfil_texto}\n"
        f"{ejercicio_txt}\n"
        f"{diagnostico}\n"
        f"{contexto_rag}\n\n"
        f"{historial_texto}\n"
        f"[Código actual del estudiante]\n"
        f"```python\n{codigo}\n```\n\n"
        f"Genera tu respuesta socrática COMPLETA en español para el intento #{intento}. "
        f"Termina SIEMPRE con UNA pregunta socrática."
    )


class AgenteTutor:
    """
    Agente 1 — Tutor Socrático.
    Intenta usar Gemini si hay créditos, si no lanza ValueError
    para que el orquestador active el modo básico.
    """

    def __init__(self, temperatura: float = 0.4):
        self.temperatura   = temperatura
        self.modelo_activo = None

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY no encontrada en .env")

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            modelos = [
                "gemini-2.0-flash-lite",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-flash-8b",
            ]
            for nombre in modelos:
                try:
                    modelo = genai.GenerativeModel(
                        model_name=nombre,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperatura,
                            max_output_tokens=1500,
                        ),
                    )
                    test = modelo.generate_content("Responde solo: ok")
                    if test.text:
                        self._modelo       = modelo
                        self.modelo_activo = nombre
                        print(f"  [AgenteTutor] Modelo activo: {nombre}")
                        break
                except Exception as e:
                    print(f"  [AgenteTutor] {nombre}: {type(e).__name__} — siguiente...")
                    continue

            if not self.modelo_activo:
                raise ValueError("Sin cuota disponible en Gemini.")

        except ImportError:
            raise ValueError("google-generativeai no instalado.")

    def responder(self, codigo, resultado_capa3, resultado_capa2, perfil,
                  intento=1, historial=None, enunciado_ejercicio=None,
                  preguntas_sin_codigo=0):
        if historial is None:
            historial = []

        contexto_rag = resultado_capa2.contexto_llm if resultado_capa2 else "Sin material relevante."
        fuentes      = resultado_capa2.fuentes if resultado_capa2 else []

        prompt = construir_prompt(
            codigo, resultado_capa3, contexto_rag, perfil, intento, historial,
            enunciado_ejercicio=enunciado_ejercicio,
            preguntas_sin_codigo=preguntas_sin_codigo,
        )

        resp  = self._modelo.generate_content(prompt)
        texto = resp.text.strip()

        return {
            "respuesta":     texto,
            "tipo_error":    resultado_capa3.get("tipo_error", "general"),
            "concepto":      resultado_capa3.get("concepto", "general"),
            "fuentes":       fuentes,
            "tokens_usados": 0,
            "modelo_usado":  self.modelo_activo,
        }
