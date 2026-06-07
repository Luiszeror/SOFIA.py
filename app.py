"""
CAPA 1 — Interfaz del Tutor Socrático SOFIA
Sistema de Tutoría Socrática UPTC

Ejecutar: streamlit run app.py
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capa4.orquestador.orquestador import Orquestador
from casos_de_prueba.repositorio import listar_conceptos

# ── Configuración de la página ────────────────────────────────────────────
st.set_page_config(
    page_title="SOFIA — Tutor Socrático Python",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.sofia-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
}
.sofia-header h1 { font-size: 2rem; font-weight: 600; margin: 0; letter-spacing: -0.5px; }
.sofia-header p  { color: #94a3b8; margin: 0.25rem 0 0; font-size: 0.95rem; }

.badge-error    { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
.badge-logico   { background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
.badge-sintaxis { background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
.badge-correcto { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
.badge-timeout  { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }

.respuesta-sofia {
    background: #f8fafc;
    border-left: 4px solid #6366f1;
    border-radius: 0 12px 12px 0;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
    font-size: 1rem;
    line-height: 1.7;
    color: #1e293b;
}
.fuente-tag {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    color: #64748b;
    display: inline-block;
    margin: 2px 3px;
}
.ejercicio-card {
    background: #fefce8;
    border: 1px solid #fde68a;
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
}
.alerta-card {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 12px;
    padding: 1rem;
}
.perfil-metric {
    text-align: center;
    padding: 0.75rem;
    background: #f8fafc;
    border-radius: 10px;
    margin-bottom: 0.5rem;
}
.perfil-metric .valor { font-size: 1.5rem; font-weight: 600; color: #1e293b; }
.perfil-metric .label { font-size: 11px; color: #64748b; }

code { font-family: 'JetBrains Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)


# ── Inicialización del estado ─────────────────────────────────────────────
if "orquestador" not in st.session_state:
    with st.spinner("Iniciando SOFIA..."):
        st.session_state.orquestador = Orquestador()

if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = []

if "intento_actual" not in st.session_state:
    st.session_state.intento_actual = 1

if "estudiante_id" not in st.session_state:
    st.session_state.estudiante_id = "estudiante_001"

if "nombre_estudiante" not in st.session_state:
    st.session_state.nombre_estudiante = "Estudiante"


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuración")

    nombre = st.text_input("Tu nombre", value=st.session_state.nombre_estudiante, key="input_nombre")
    if nombre != st.session_state.nombre_estudiante:
        st.session_state.nombre_estudiante = nombre
        st.session_state.estudiante_id = nombre.lower().replace(" ", "_")

    concepto = st.selectbox(
        "Concepto a practicar",
        options=listar_conceptos(),
        format_func=lambda x: x.replace("_", " ").title(),
    )

    modo_libre = st.toggle(
        "Modo libre (sin casos de prueba)",
        value=False,
        help="Evalúa cualquier código Python sin comparar contra casos. Solo detecta errores de sintaxis y runtime.",
    )

    st.markdown("---")
    st.markdown("### Cómo usar SOFIA")
    st.markdown("""
    1. Escribe tu código Python
    2. Haz clic en **Evaluar**
    3. SOFIA te guiará con preguntas
    4. Nunca te dará la respuesta directa
    5. Escribe `FIN` para terminar
    """)

    st.markdown("---")
    llm_activo = st.session_state.orquestador._llm_disponible
    if llm_activo:
        st.success("LLM activo (Gemini 1.5 Flash)")
    else:
        st.warning("Sin API key — modo básico")
        st.caption("Agrega GOOGLE_API_KEY en .env para activar el tutor completo")

    if st.button("Nueva sesión", type="secondary"):
        st.session_state.historial_chat = []
        st.session_state.intento_actual = 1
        st.rerun()


# ── Cabecera principal ────────────────────────────────────────────────────
st.markdown("""
<div class="sofia-header">
    <h1>🐍 SOFIA — Tutor Socrático Python</h1>
    <p>Sistema de tutoría adaptativa · UPTC · Ingeniería de Sistemas</p>
</div>
""", unsafe_allow_html=True)

col_chat, col_perfil = st.columns([2, 1])

# ── Columna izquierda: Chat ───────────────────────────────────────────────
with col_chat:
    st.markdown(f"**Practicando:** `{concepto.replace('_', ' ').title()}` · Intento #{st.session_state.intento_actual}")

    if not modo_libre:
        from casos_de_prueba.repositorio import obtener_ejercicio
        ej = obtener_ejercicio(concepto, 0)
        if ej:
            st.info(f"**Ejercicio:** {ej['descripcion']}")

    # Editor de código
    codigo = st.text_area(
        "Escribe tu código Python aquí",
        height=200,
        placeholder=f"# Escribe tu solución para el concepto: {concepto}\n",
        key="editor_codigo",
        help="Escribe código Python y presiona Evaluar",
    )

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        evaluar = st.button("Evaluar ↗", type="primary", use_container_width=True)
    with col_btn2:
        st.caption(f"El sistema evaluará tu código contra los casos de prueba de `{concepto}`")

    # Procesar evaluación
    if evaluar and codigo.strip():
        with st.spinner("SOFIA está analizando tu código..."):
            resultado = st.session_state.orquestador.procesar(
                codigo            = codigo,
                concepto          = concepto,
                estudiante_id     = st.session_state.estudiante_id,
                nombre_estudiante = st.session_state.nombre_estudiante,
                intento           = st.session_state.intento_actual,
                historial         = st.session_state.historial_chat,
                modo_libre        = modo_libre,
            )

        # Guardar en historial
        st.session_state.historial_chat.append({
            "role": "user",
            "content": f"[Intento #{st.session_state.intento_actual}]\n```python\n{codigo}\n```"
        })
        st.session_state.historial_chat.append({
            "role": "assistant",
            "content": resultado["respuesta_tutor"]
        })
        st.session_state.intento_actual += 1

        # Guardar último resultado
        st.session_state.ultimo_resultado = resultado

    # Mostrar historial del chat
    if st.session_state.historial_chat:
        st.markdown("---")
        st.markdown("#### Sesión actual")

        for i, msg in enumerate(st.session_state.historial_chat):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🐍"):
                    # Badge del tipo de error
                    if "ultimo_resultado" in st.session_state and i == len(st.session_state.historial_chat) - 1:
                        r = st.session_state.ultimo_resultado
                        tipo = r["tipo_error"]
                        badge_class = {
                            "correcto":       "badge-correcto",
                            "error_logico":   "badge-logico",
                            "error_sintaxis": "badge-sintaxis",
                            "error_runtime":  "badge-error",
                            "error_timeout":  "badge-timeout",
                            "error_seguridad":"badge-sintaxis",
                        }.get(tipo, "badge-logico")

                        st.markdown(
                            f'<span class="{badge_class}">{tipo.replace("_", " ").upper()}</span> '
                            f'&nbsp; {r["casos_pasados"]}/{r["casos_total"]} casos ✓',
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f'<div class="respuesta-sofia">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )

                    # Fuentes del RAG
                    if "ultimo_resultado" in st.session_state and i == len(st.session_state.historial_chat) - 1:
                        fuentes = st.session_state.ultimo_resultado.get("fuentes", [])
                        if fuentes:
                            fuentes_html = " ".join([f'<span class="fuente-tag">📖 {f}</span>' for f in fuentes])
                            st.markdown(fuentes_html, unsafe_allow_html=True)

        # Ejercicio nuevo propuesto por el Generador
        if "ultimo_resultado" in st.session_state:
            ej = st.session_state.ultimo_resultado.get("ejercicio_nuevo")
            if ej:
                st.markdown(f"""
                <div class="ejercicio-card">
                    <strong>Ejercicio adicional sugerido por SOFIA</strong><br>
                    <em>Concepto: {ej['concepto'].replace('_',' ').title()} · Dificultad: {ej['dificultad']}</em><br><br>
                    {ej['enunciado']}<br><br>
                    <small>💡 Pista inicial: {ej['pista']}</small>
                </div>
                """, unsafe_allow_html=True)


# ── Columna derecha: Perfil del estudiante ────────────────────────────────
with col_perfil:
    st.markdown("#### Tu perfil de aprendizaje")

    if "ultimo_resultado" in st.session_state:
        perfil = st.session_state.ultimo_resultado.get("perfil", {})

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="perfil-metric">
                <div class="valor">{perfil.get('interacciones', 0)}</div>
                <div class="label">Interacciones</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            score = perfil.get('score_riesgo', 0)
            color = "#ef4444" if score >= 6.5 else "#f59e0b" if score >= 4 else "#22c55e"
            st.markdown(f"""
            <div class="perfil-metric">
                <div class="valor" style="color:{color}">{score}</div>
                <div class="label">Score riesgo</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="perfil-metric">
            <div class="valor">{perfil.get('intentos_promedio', 0)}</div>
            <div class="label">Intentos promedio</div>
        </div>""", unsafe_allow_html=True)

        # Errores frecuentes
        errores = perfil.get("errores_frecuentes", [])
        if errores:
            st.markdown("**Conceptos con más dificultad:**")
            for concepto_err in errores:
                num = perfil.get("errores_por_concepto", {}).get(concepto_err, 0)
                st.markdown(f"- `{concepto_err}` — {num} error(es)")

        # Alerta
        if perfil.get("en_alerta"):
            st.markdown("""
            <div class="alerta-card">
                <strong>Atención requerida</strong><br>
                Tu docente ha sido notificado para ofrecerte ayuda adicional.
            </div>""", unsafe_allow_html=True)

        # Info del RAG
        st.markdown("---")
        st.markdown("#### Material usado")
        fuentes = st.session_state.ultimo_resultado.get("fuentes", [])
        if fuentes:
            for f in fuentes:
                st.caption(f"📖 {f}")
        else:
            st.caption("Sin fuentes recuperadas aún")

        # Modo LLM
        st.markdown("---")
        modo = "LLM activo" if st.session_state.ultimo_resultado.get("llm_activo") else "Modo básico"
        st.caption(f"Modo: {modo}")
        st.caption(f"Tiempo RAG: {st.session_state.ultimo_resultado.get('tiempo_ms', 0)} ms")
    else:
        st.info("Evalúa tu primer código para ver tu perfil aquí.")
        st.markdown("""
        El perfil muestra:
        - Interacciones totales
        - Score de riesgo (0-10)
        - Intentos promedio
        - Conceptos con dificultad
        """)
