"""
AGENTE 1 — Tutor Socrático
Capa 4 — Sistema de Tutoría Socrática UPTC

Usa Google Gemini API (gratuito con cuenta Google).
Modelo: gemini-1.5-flash (rápido y gratuito)
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT_SOCRATICO = """Eres SOFIA, un tutor de Python que sigue el método socrático estrictamente.

REGLAS ABSOLUTAS:
1. NUNCA escribas código corregido directamente.
2. NUNCA des la respuesta al ejercicio.
3. SIEMPRE termina tu respuesta con UNA sola pregunta que guíe al estudiante.
4. Si el estudiante lleva más de 2 intentos fallidos, baja el nivel de abstracción — pregunta sobre una línea específica del código.
5. Usa el material del curso (entre === MATERIAL ===) para anclar tus preguntas a ejemplos que el estudiante ya vio.
6. Sé cálido y alentador. El error es parte del aprendizaje.
7. Máximo 4 oraciones + la pregunta final. Sin listas, sin código.

ESTILO DE PREGUNTA SEGÚN INTENTO:
- Intento 1-2: Pregunta conceptual amplia.
- Intento 3-4: Pregunta sobre línea específica del código.
- Intento 5+: Pista muy concreta sin dar la solución.

NUNCA uses: La respuesta es... / Deberías escribir... / El código correcto es...
"""


def construir_prompt_completo(codigo, resultado_capa3, contexto_rag, perfil, intento, historial):
    """
    Gemini usa un solo string de prompt — combinamos todo aquí.
    """
    perfil_texto = ""
    if perfil.get("errores_frecuentes"):
        errores = ", ".join(perfil["errores_frecuentes"][:3])
        perfil_texto = (
            f"\n[Perfil del estudiante]\n"
            f"Errores frecuentes en: {errores}\n"
            f"Intentos promedio: {perfil.get('intentos_promedio', 'N/A')}\n"
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

    # Historial de conversación como texto
    historial_texto = ""
    if historial:
        historial_texto = "\n[Conversación previa]\n"
        for msg in historial[-4:]:
            rol = "Estudiante" if msg["role"] == "user" else "SOFIA"
            historial_texto += f"{rol}: {msg['content'][:200]}\n"

    return (
        f"{SYSTEM_PROMPT_SOCRATICO}\n\n"
        f"{perfil_texto}\n"
        f"{diagnostico}\n"
        f"{contexto_rag}\n\n"
        f"{historial_texto}\n"
        f"[Código actual del estudiante]\n"
        f"```python\n{codigo}\n```\n\n"
        f"Genera tu respuesta socrática para el intento #{intento}. "
        f"Recuerda: máximo 4 oraciones y termina con UNA pregunta."
    )


class AgenteTutor:
    """Agente 1 — Tutor Socrático usando Google Gemini (gratuito)."""

    def __init__(self, modelo: str = "gemini-2.0-flash", temperatura: float = 0.4):
        self.modelo_nombre = modelo
        self.temperatura   = temperatura
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY no encontrada en .env")
        genai.configure(api_key=api_key)
        self.modelo = genai.GenerativeModel(
            model_name=modelo,
            generation_config=genai.types.GenerationConfig(
                temperature=temperatura,
                max_output_tokens=400,
            ),
        )

    def responder(self, codigo, resultado_capa3, resultado_capa2, perfil, intento=1, historial=None):
        if historial is None:
            historial = []

        contexto_rag = resultado_capa2.contexto_llm if resultado_capa2 else "Sin material relevante."
        fuentes      = resultado_capa2.fuentes if resultado_capa2 else []

        prompt = construir_prompt_completo(
            codigo, resultado_capa3, contexto_rag, perfil, intento, historial
        )

        respuesta = self.modelo.generate_content(prompt)
        texto     = respuesta.text.strip()

        return {
            "respuesta":     texto,
            "tipo_error":    resultado_capa3.get("tipo_error", "general"),
            "concepto":      resultado_capa3.get("concepto", "general"),
            "fuentes":       fuentes,
            "tokens_usados": 0,  # Gemini no expone tokens en esta versión
        }
