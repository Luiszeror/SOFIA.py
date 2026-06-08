"""
CAPA 1 — Interfaz SOFIA.py
Sistema de Tutoría Socrática UPTC
Ejecutar: streamlit run app.py
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capa4.orquestador.orquestador import Orquestador
from casos_de_prueba.repositorio import listar_conceptos, obtener_ejercicio, listar_ejercicios

st.set_page_config(page_title="SOFIA.py", page_icon="🐍", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.login-wrap{max-width:420px;margin:4rem auto;padding:2.5rem;background:white;
  border-radius:20px;box-shadow:0 8px 40px rgba(0,0,0,.10);border:1px solid #e2e8f0;}
.login-logo{text-align:center;font-size:3rem;margin-bottom:.5rem;}
.login-title{text-align:center;font-size:1.6rem;font-weight:700;color:#1e3a5f;margin-bottom:.25rem;}
.login-sub{text-align:center;color:#64748b;font-size:.9rem;margin-bottom:1.5rem;}
.chat-header{background:linear-gradient(135deg,#1a1a2e 0%,#0f3460 100%);
  padding:1rem 1.5rem;border-radius:14px;margin-bottom:1rem;color:white;}
.chat-header h2{font-size:1.1rem;font-weight:600;margin:0;}
.chat-header p{font-size:.8rem;color:#94a3b8;margin:0;}
.msg-sofia{background:#f8fafc;border-left:4px solid #6366f1;border-radius:0 14px 14px 0;
  padding:1rem 1.25rem;margin:.5rem 0;font-size:.97rem;line-height:1.75;color:#1e293b;}
.msg-user{background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 14px 14px 0;
  padding:.75rem 1.25rem;margin:.5rem 0;font-size:.95rem;color:#1e40af;}
.output-box{background:#0f172a;color:#e2e8f0;font-family:'JetBrains Mono',monospace;
  font-size:.82rem;padding:.75rem 1rem;border-radius:8px;margin:.4rem 0;line-height:1.5;}
.badge-correcto{background:#dcfce7;color:#166534;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge-logico{background:#dbeafe;color:#1e40af;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge-sintaxis{background:#fef9c3;color:#854d0e;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge-runtime{background:#fee2e2;color:#991b1b;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge-timeout{background:#fee2e2;color:#991b1b;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge-seguridad{background:#fef9c3;color:#854d0e;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.fuente-tag{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:6px;
  padding:2px 8px;font-size:10px;color:#64748b;display:inline-block;margin:2px 3px;}
.ejercicio-card{background:#fefce8;border:1px solid #fde68a;border-radius:12px;padding:1rem;margin:.5rem 0;}
.perfil-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:.75rem;text-align:center;}
.perfil-box .val{font-size:1.4rem;font-weight:700;color:#1e293b;}
.perfil-box .lbl{font-size:10px;color:#64748b;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════
if "sesion_iniciada" not in st.session_state:
    st.session_state.sesion_iniciada = False

if not st.session_state.sesion_iniciada:
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">🐍</div>
        <div class="login-title">SOFIA.py</div>
        <div class="login-sub">Sistema de Tutoría Socrática · UPTC</div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        nombre_inp   = st.text_input("Tu nombre", placeholder="Ej: Luis Esteban")
        semestre_inp = st.selectbox("Semestre", list(range(1, 11)),
                                    format_func=lambda x: f"Semestre {x}")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Comenzar sesión →", type="primary", use_container_width=True):
            if not nombre_inp.strip():
                st.error("Por favor escribe tu nombre.")
            else:
                st.session_state.update({
                    "sesion_iniciada":      True,
                    "nombre_estudiante":    nombre_inp.strip(),
                    "semestre":             semestre_inp,
                    "estudiante_id":        nombre_inp.strip().lower().replace(" ", "_"),
                    "historial_chat":       [],
                    "intento_actual":       1,
                    "modo_actual":          None,
                    "concepto_actual":      None,
                    "ejercicio_idx":        0,
                    "esperando_resp":       False,
                    "preguntas_sin_codigo": 0,
                })
                st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════
# SESIÓN INICIADA
# ══════════════════════════════════════════════════════════════════════════
nombre   = st.session_state.nombre_estudiante
semestre = st.session_state.semestre

if "orquestador" not in st.session_state:
    with st.spinner("Iniciando SOFIA..."):
        st.session_state.orquestador = Orquestador()

orch = st.session_state.orquestador

def agregar_msg(rol, contenido, extra=None):
    st.session_state.historial_chat.append(
        {"role": rol, "content": contenido, "extra": extra or {}}
    )

def menu_txt():
    return (
        f"¿Qué quieres hacer ahora, **{nombre}**?\n\n"
        "**1.** Practicar con ejercicios guiados\n"
        "**2.** Modo libre — evalúa cualquier código\n"
        "**3.** Hacer una pregunta conceptual"
    )

# Bienvenida inicial
if not st.session_state.historial_chat:
    agregar_msg("assistant",
        f"¡Hola **{nombre}**! Soy SOFIA, tu tutora de Python 🐍\n\n"
        f"Estás en **semestre {semestre}**. Nunca te daré las respuestas directamente — "
        f"te haré las preguntas correctas para que las descubras tú mismo.\n\n"
        + menu_txt()
    )

col_chat, col_perfil = st.columns([2.2, 1])

# ── COLUMNA CHAT ──────────────────────────────────────────────────────────
with col_chat:
    llm_txt = (f"LLM: {getattr(orch.tutor, 'modelo_activo', '—')}"
               if orch._llm_disponible else "Modo básico")
    st.markdown(f"""
    <div class="chat-header">
        <span style="font-size:2rem">🐍</span>
        <div><h2>SOFIA.py — Tutor Socrático</h2>
        <p>Hola <b>{nombre}</b> · Semestre {semestre} · {llm_txt}</p></div>
    </div>""", unsafe_allow_html=True)

    # Renderizar historial
    for msg in st.session_state.historial_chat:
        if msg["role"] == "assistant":
            # Escapar markdown del corpus que se cuela en las respuestas
            contenido_seguro = (msg["content"]
                .replace("##", "")
                .replace("# ", "")
            )
            st.markdown(f'<div class="msg-sofia">{contenido_seguro}</div>',
                        unsafe_allow_html=True)
            ex = msg.get("extra", {})

            # Consola Python estilo terminal
            consola_val = ex.get("consola_output", "") or ex.get("stdout_codigo", "")
            if consola_val and str(consola_val) not in ("", "None"):
                tipo_err = ex.get("tipo_error","")
                icono = "✗" if "error" in tipo_err else "▶"
                color = "#f87171" if "error" in tipo_err else "#86efac"
                salida = str(consola_val).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
                st.markdown(
                    f'''<div class="output-box">
                    <span style="color:{color};font-weight:600">{icono} Consola Python</span><br>
                    <span style="color:#e2e8f0">{salida}</span>
                    </div>''',
                    unsafe_allow_html=True,
                )

            # Badge tipo error
            if ex.get("tipo_error"):
                tipo = ex["tipo_error"]
                cls  = tipo.replace("error_", "")
                cp   = ex.get("casos_pasados", 0)
                ct   = ex.get("casos_total", 0)
                casos_txt = f"&nbsp;·&nbsp;{cp}/{ct} casos ✓" if ct > 0 else ""
                st.markdown(
                    f'<span class="badge-{cls}">{tipo.replace("_"," ").upper()}</span>{casos_txt}',
                    unsafe_allow_html=True)

            # Fuentes RAG
            if ex.get("fuentes"):
                html = " ".join([f'<span class="fuente-tag">📖 {f}</span>'
                                 for f in ex["fuentes"]])
                st.markdown(html, unsafe_allow_html=True)

            # Ejercicio sugerido
            if ex.get("ejercicio_nuevo"):
                ej = ex["ejercicio_nuevo"]
                st.markdown(f"""
                <div class="ejercicio-card">
                    <b>💡 Ejercicio adicional sugerido por SOFIA</b><br>
                    <em>{ej['concepto'].replace('_',' ').title()} · {ej['dificultad']}</em>
                    <br><br>{ej['enunciado']}<br><br>
                    <small>Pista: {ej['pista']}</small>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="msg-user">👤 {msg["content"]}</div>',
                        unsafe_allow_html=True)

    st.markdown("---")

    modo            = st.session_state.modo_actual
    concepto_actual = st.session_state.concepto_actual or "general"

    # ── MENÚ PRINCIPAL ────────────────────────────────────────────────────
    if modo is None:
        inp = st.chat_input("Escribe 1, 2 o 3...")
        if inp:
            inp = inp.strip()
            agregar_msg("user", inp)
            if inp == "1":
                st.session_state.modo_actual = "ejercicios"
                conceptos = listar_conceptos()
                opts = "\n".join([f"**{i+1}.** {c.replace('_',' ').title()}"
                                  for i, c in enumerate(conceptos)])
                agregar_msg("assistant", f"¿Qué concepto quieres practicar?\n\n{opts}")
            elif inp == "2":
                st.session_state.modo_actual = "libre"
                agregar_msg("assistant",
                    "Modo libre activado 🟢\n\n"
                    "Escribe tu código en el editor. También puedes responder "
                    "mis preguntas o escribir **¿tu pregunta?** para consultarme algo.\n\n"
                    "Escribe **menu** para volver al inicio.")
            elif inp == "3":
                st.session_state.modo_actual = "pregunta"
                agregar_msg("assistant",
                    "¿Cuál es tu pregunta? Escríbela directamente 👇")
            else:
                agregar_msg("assistant",
                    f"Por favor escribe **1**, **2** o **3**.\n\n{menu_txt()}")
            st.rerun()

    # ── SELECCIÓN DE CONCEPTO ─────────────────────────────────────────────
    elif modo == "ejercicios" and st.session_state.concepto_actual is None:
        inp = st.chat_input("Escribe el número del concepto...")
        if inp:
            agregar_msg("user", inp.strip())
            conceptos = listar_conceptos()
            try:
                idx = int(inp.strip()) - 1
                if 0 <= idx < len(conceptos):
                    concepto = conceptos[idx]
                    st.session_state.concepto_actual      = concepto
                    st.session_state.ejercicio_idx        = 0
                    st.session_state.intento_actual       = 1
                    st.session_state.preguntas_sin_codigo = 0
                    ej       = obtener_ejercicio(concepto, 0)
                    ejercicios = listar_ejercicios(concepto)
                    lista_ej = "\n".join([f"**{i+1}.** {e}"
                                          for i, e in enumerate(ejercicios)])
                    agregar_msg("assistant",
                        f"Concepto: **{concepto.replace('_',' ').title()}** ✓\n\n"
                        f"Ejercicios disponibles:\n{lista_ej}\n\n"
                        f"Empezamos con el primero:\n\n"
                        f"📝 **{ej['nombre']}**\n\n{ej['descripcion']}\n\n"
                        f"Escribe tu código abajo cuando estés listo. "
                        f"Si tienes dudas, usa el campo de preguntas.")
                else:
                    agregar_msg("assistant",
                        f"Elige un número entre 1 y {len(conceptos)}.")
            except ValueError:
                agregar_msg("assistant", "Escribe el número del concepto.")
            st.rerun()

    # ── MODO EJERCICIOS / LIBRE ───────────────────────────────────────────
    elif modo in ("ejercicios", "libre"):
        ej_actual = (obtener_ejercicio(concepto_actual, st.session_state.ejercicio_idx)
                     if st.session_state.concepto_actual else None)

        if ej_actual:
            st.info(f"📝 **{ej_actual['nombre']}** — {ej_actual['descripcion']}")

        # Editor de código
        codigo = st.text_area(
            "Editor de código Python",
            height=180,
            placeholder="# Escribe tu código aquí...",
            key=f"editor_{st.session_state.intento_actual}_{modo}",
        )

        col_ev, col_info = st.columns([1, 2])
        with col_ev:
            evaluar = st.button("Evaluar código ↗", type="primary",
                                use_container_width=True)
        with col_info:
            st.caption(f"Concepto: `{concepto_actual}` · Intento #{st.session_state.intento_actual}")

        if evaluar and codigo.strip():
            agregar_msg("user", f"```python\n{codigo}\n```")
            with st.spinner("SOFIA analiza tu código..."):
                ej_actual_data = obtener_ejercicio(concepto_actual, st.session_state.ejercicio_idx) if st.session_state.concepto_actual else None
                resultado = orch.procesar(
                    codigo               = codigo,
                    concepto             = concepto_actual,
                    estudiante_id        = st.session_state.estudiante_id,
                    nombre_estudiante    = nombre,
                    intento              = st.session_state.intento_actual,
                    historial            = [{"role": m["role"], "content": m["content"]}
                                            for m in st.session_state.historial_chat],
                    modo_libre           = (modo == "libre"),
                    semestre             = semestre,
                    enunciado_ejercicio  = ej_actual_data,
                    preguntas_sin_codigo = st.session_state.get("preguntas_sin_codigo", 0),
                )
                # Resetear contador al enviar código
                st.session_state.preguntas_sin_codigo = 0
            st.session_state.intento_actual += 1
            agregar_msg("assistant", resultado["respuesta_tutor"], extra={
                "tipo_error":     resultado["tipo_error"],
                "casos_pasados":  resultado.get("casos_pasados", 0),
                "casos_total":    resultado.get("casos_total", 0),
                "fuentes":        resultado.get("fuentes", []),
                "ejercicio_nuevo":resultado.get("ejercicio_nuevo"),
                "stdout_codigo":  resultado.get("stdout_codigo", ""),
                "consola_output": resultado.get("consola_output", ""),
            })
            # Avanzar al siguiente ejercicio si fue correcto
            if resultado["tipo_error"] == "correcto" and modo == "ejercicios":
                ejercicios = listar_ejercicios(concepto_actual)
                sig_idx = st.session_state.ejercicio_idx + 1
                if sig_idx < len(ejercicios):
                    st.session_state.ejercicio_idx  = sig_idx
                    st.session_state.intento_actual = 1
                    ej_sig = obtener_ejercicio(concepto_actual, sig_idx)
                    agregar_msg("assistant",
                        f"¡Vamos al siguiente! 🎯\n\n"
                        f"📝 **{ej_sig['nombre']}**\n\n{ej_sig['descripcion']}")
                else:
                    agregar_msg("assistant",
                        f"🏆 ¡Completaste todos los ejercicios de "
                        f"**{concepto_actual.replace('_',' ').title()}**!\n\n"
                        + menu_txt())
                    st.session_state.modo_actual     = None
                    st.session_state.concepto_actual = None
            st.rerun()

        # Campo para responder preguntas de SOFIA o hacer preguntas conceptuales
        st.markdown("**Responde a SOFIA o haz una pregunta con ¿...?**")
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            resp_txt = st.text_input("Respuesta o pregunta",
                placeholder="Tu respuesta a SOFIA, o ¿tu pregunta conceptual?",
                label_visibility="collapsed",
                key=f"resp_{st.session_state.intento_actual}")
        with col_r2:
            enviar_resp = st.button("Enviar →", use_container_width=True,
                                    key=f"btn_resp_{st.session_state.intento_actual}")

        if enviar_resp and resp_txt.strip():
            texto = resp_txt.strip()
            agregar_msg("user", texto)
            if texto.lower() == "menu":
                st.session_state.modo_actual         = None
                st.session_state.concepto_actual     = None
                st.session_state.intento_actual      = 1
                st.session_state.preguntas_sin_codigo = 0
                agregar_msg("assistant", menu_txt())
            else:
                # Incrementar contador de preguntas sin código
                st.session_state.preguntas_sin_codigo = st.session_state.get("preguntas_sin_codigo", 0) + 1
                psc = st.session_state.preguntas_sin_codigo
                ej_act = obtener_ejercicio(concepto_actual, st.session_state.ejercicio_idx) if st.session_state.concepto_actual else None

                with st.spinner("SOFIA responde..."):
                    r = orch.responder_pregunta(
                        pregunta             = texto,
                        concepto_hint        = concepto_actual,
                        estudiante_id        = st.session_state.estudiante_id,
                        nombre_estudiante    = nombre,
                        historial            = [{"role": m["role"], "content": m["content"]}
                                               for m in st.session_state.historial_chat],
                        semestre             = semestre,
                        preguntas_sin_codigo = psc,
                        enunciado_ejercicio  = ej_act,
                    )
                agregar_msg("assistant", r["respuesta"],
                            extra={"fuentes": r.get("fuentes", [])})
                # Si SOFIA confirma que la respuesta fue correcta, bajar score
                texto_resp = r["respuesta"].lower()
                if any(p in texto_resp for p in ["correcto", "exacto", "excelente",
                       "muy bien", "perfecto", "así es", "en efecto", "tienes razón"]):
                    perfil_act = orch.analista.cargar_perfil(
                        st.session_state.estudiante_id, nombre, semestre)
                    orch.analista.registrar_respuesta_correcta(perfil_act, concepto_actual)
            st.rerun()

        # Chat input — menú o ¿preguntas?
        inp2 = st.chat_input("Escribe 'menu' para volver o ¿tu pregunta?")
        if inp2:
            inp2 = inp2.strip()
            if inp2.lower() == "menu":
                agregar_msg("user", "menu")
                st.session_state.modo_actual     = None
                st.session_state.concepto_actual = None
                st.session_state.intento_actual  = 1
                agregar_msg("assistant", menu_txt())
                st.rerun()

    # ── MODO PREGUNTA DIRECTA ─────────────────────────────────────────────
    elif modo == "pregunta":
        inp = st.chat_input("Escribe tu pregunta aquí...")
        if inp:
            agregar_msg("user", f"❓ {inp}")
            with st.spinner("SOFIA busca en el material..."):
                r = orch.responder_pregunta(
                    pregunta=inp, concepto_hint="general",
                    estudiante_id=st.session_state.estudiante_id,
                    nombre_estudiante=nombre,
                    historial=[{"role": m["role"], "content": m["content"]}
                               for m in st.session_state.historial_chat[-6:]],
                )
            agregar_msg("assistant", r["respuesta"],
                        extra={"fuentes": r.get("fuentes", [])})
            agregar_msg("assistant", menu_txt())
            st.session_state.modo_actual = None
            st.rerun()

# ── COLUMNA PERFIL ────────────────────────────────────────────────────────
with col_perfil:
    st.markdown("#### Tu perfil")
    perfil = orch.analista.cargar_perfil(st.session_state.estudiante_id, nombre)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="perfil-box">
            <div class="val">{perfil.interacciones}</div>
            <div class="lbl">Interacciones</div></div>""", unsafe_allow_html=True)
    with c2:
        score = perfil.score_riesgo
        color = "#ef4444" if score >= 6.5 else "#f59e0b" if score >= 4 else "#22c55e"
        st.markdown(f"""<div class="perfil-box">
            <div class="val" style="color:{color}">{score}</div>
            <div class="lbl">Score riesgo</div></div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="perfil-box" style="margin-top:.5rem">
        <div class="val">{perfil.intentos_promedio}</div>
        <div class="lbl">Intentos promedio</div></div>""", unsafe_allow_html=True)

    if perfil.errores_frecuentes:
        st.markdown("**Dificultades:**")
        for c in perfil.errores_frecuentes:
            num = perfil.errores_por_concepto.get(c, 0)
            st.markdown(f"- `{c}` — {num} error(es)")

    if perfil.en_alerta:
        st.error("⚠️ Tu docente ha sido notificado.")

    st.markdown("---")
    st.caption(f"Semestre: {semestre}")
    st.caption(f"Modo: {'LLM activo' if orch._llm_disponible else 'Básico'}")

    if st.button("Cerrar sesión", type="secondary", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
