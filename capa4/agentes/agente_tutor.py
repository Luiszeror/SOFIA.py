"""
AGENTE 1 — Tutor Socrático
Capa 4 — Sistema de Tutoría Socrática UPTC

LLM: Google Gemini
Modelos en orden: gemini-2.5-flash → gemini-2.5-flash-lite → gemini-2.0-flash-lite → gemini-2.0-flash
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

MODELOS_FALLBACK = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

SYSTEM_PROMPT_SOCRATICO = """Eres SOFIA, un tutor socrático de Python. Respondes SIEMPRE en español.
Tienes acceso al historial completo de la conversación — ÚSALO SIEMPRE.

REGLA PRINCIPAL: NO expliques directamente. SIEMPRE guía al estudiante a descubrir la respuesta mediante preguntas.

REGLAS ABSOLUTAS:
1. NUNCA des la respuesta directamente ni expliques el concepto completo.
2. NUNCA escribas código corregido completo.
3. SIEMPRE termina con exactamente UNA pregunta socrática.
4. El material del curso ya se mostró al estudiante — úsalo para formular preguntas, no para repetirlo.
5. Máximo 3 oraciones + la pregunta final.
6. Usa analogías del mundo real para guiar sin revelar.
7. SCOPE DEL CURSO: Solo respondes preguntas sobre Python. Si el estudiante pregunta sobre Java, C++, JavaScript u otro lenguaje, responde amablemente que este curso es de Python y redirige: "Este curso se enfoca en Python. ¿Te gustaría explorar el concepto equivalente en Python?"

ESTILO SOCRÁTICO ESTRICTO — en vez de explicar, PREGUNTA:
❌ MAL: "Un diccionario almacena pares clave:valor. Las claves deben ser únicas..."
✅ BIEN: "¿Has visto alguna vez una agenda telefónica donde cada nombre tiene un número? ¿Cómo crees que Python podría representar esa misma idea?"

❌ MAL: "El error es que usas print en vez de return..."
✅ BIEN: "Tu función ejecuta y muestra algo en pantalla. Pero el ejercicio necesita usar ese valor después. ¿Qué diferencia hay entre mostrar algo y devolverlo?"

FLUJO PROGRESIVO SEGÚN PREGUNTAS SIN CÓDIGO:
- Pregunta 1: Analogía del mundo real + pregunta amplia sobre el concepto.
- Pregunta 2: Conectar con lo que respondió + pregunta más específica sobre el ejercicio.
- Pregunta 3+: Pista muy concreta + invitar a escribir: "¿Lo intentamos en código?"

CUANDO HAY CÓDIGO CON ERROR:
- Una oración sobre qué observas en el código (sin decir el error directamente).
- Conectar con conversación previa si existe.
- Pregunta específica sobre la línea problemática.

CUANDO EL CÓDIGO ES CORRECTO:
- Felicitar brevemente y conectar con el proceso de aprendizaje.
- Pregunta de consolidación: "¿Podrías explicar con tus palabras por qué funciona?"

FLUJO DE EVALUACIÓN CONJUNTA:
- Referenciar conversación previa: "Como exploramos antes...".
- Cada respuesta acerca más al estudiante a la solución mediante preguntas."""


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
    """Agente 1 — Tutor Socrático usando Google Gemini."""

    def __init__(self, temperatura: float = 0.4):
        self.temperatura   = temperatura
        self.modelo_activo = None
        self._modelo       = None

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY no encontrada en .env")

        genai.configure(api_key=api_key)

        for nombre in MODELOS_FALLBACK:
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
            raise ValueError("Ningún modelo de Gemini disponible.")

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

        for nombre in [self.modelo_activo] + [m for m in MODELOS_FALLBACK if m != self.modelo_activo]:
            try:
                modelo_temp = genai.GenerativeModel(
                    model_name=nombre,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperatura,
                        max_output_tokens=1500,
                    ),
                )
                resp  = modelo_temp.generate_content(prompt)
                texto = resp.text.strip()
                if nombre != self.modelo_activo:
                    print(f"  [AgenteTutor] Cambiando a: {nombre}")
                    self._modelo       = modelo_temp
                    self.modelo_activo = nombre
                return {
                    "respuesta":     texto,
                    "tipo_error":    resultado_capa3.get("tipo_error", "general"),
                    "concepto":      resultado_capa3.get("concepto", "general"),
                    "fuentes":       fuentes,
                    "tokens_usados": 0,
                    "modelo_usado":  nombre,
                }
            except Exception as e:
                print(f"  [AgenteTutor] {nombre} falló: {type(e).__name__} — siguiente...")
                continue

        raise ValueError("Ningún modelo de Gemini respondió.")
