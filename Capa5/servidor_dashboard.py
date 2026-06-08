"""
servidor_dashboard.py — Capa 5
Servidor del dashboard docente de SOFIA.py

Ejecutar desde ProyectoFinal/:
    python capa5/servidor_dashboard.py

Luego abrir en el navegador:
    http://localhost:8503
"""

import http.server
import json
import os
import hashlib
import urllib.parse
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────
RAIZ           = Path(__file__).parent.parent
DIR_PERFILES   = RAIZ / "data" / "perfiles"
DOCENTES_JSON  = Path(__file__).parent / "docentes.json"
PORT           = 8503

# ── Credenciales ──────────────────────────────────────────────────────────
def cargar_docentes():
    if DOCENTES_JSON.exists():
        with open(DOCENTES_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {}

def verificar_credenciales(usuario, password):
    docentes = cargar_docentes()
    if usuario not in docentes:
        return None
    hash_pwd = hashlib.sha256(password.encode()).hexdigest()
    if docentes[usuario]["password_hash"] == hash_pwd:
        return docentes[usuario]
    return None

# ── Leer perfiles ─────────────────────────────────────────────────────────
def cargar_perfiles(semestres_permitidos=None):
    perfiles = []
    if not DIR_PERFILES.exists():
        return perfiles
    for archivo in sorted(DIR_PERFILES.glob("*.json")):
        try:
            with open(archivo, encoding="utf-8") as f:
                p = json.load(f)
            if semestres_permitidos:
                if p.get("semestre", 1) not in semestres_permitidos:
                    continue
            perfiles.append(p)
        except Exception:
            continue
    return perfiles

# ── HTML del dashboard ────────────────────────────────────────────────────
def html_dashboard(docente):
    perfiles      = cargar_perfiles(docente.get("semestres"))
    perfiles_json = json.dumps(perfiles, ensure_ascii=False)
    semestres     = docente.get("semestres", list(range(1, 11)))
    opts_sem      = "\n".join(
        [f'<option value="{s}">Semestre {s}</option>' for s in semestres]
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOFIA.py — Panel Docente</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{{--azul:#1e3a5f;--azul-med:#2563eb;--azul-claro:#dbeafe;--verde:#166534;
  --verde-bg:#dcfce7;--rojo:#991b1b;--rojo-bg:#fee2e2;--ambar:#854d0e;
  --ambar-bg:#fef9c3;--gris-bg:#f8fafc;--gris-bd:#e2e8f0;--texto:#1e293b;--texto-2:#64748b;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',sans-serif;background:var(--gris-bg);color:var(--texto);}}
.topbar{{background:linear-gradient(90deg,#1a1a2e,#0f3460);color:white;padding:.9rem 2rem;
  display:flex;align-items:center;justify-content:space-between;}}
.topbar h1{{font-size:1.1rem;font-weight:600;}}
.topbar span{{font-size:.8rem;color:#94a3b8;}}
.btn-logout{{background:rgba(255,255,255,.12);color:white;border:1px solid rgba(255,255,255,.2);
  padding:.4rem 1rem;border-radius:8px;cursor:pointer;font-size:.85rem;text-decoration:none;}}
.btn-logout:hover{{background:rgba(255,255,255,.2);}}
.main{{padding:1.5rem 2rem;max-width:1400px;margin:0 auto;}}
.filters{{display:flex;gap:12px;align-items:center;margin-bottom:1.25rem;flex-wrap:wrap;}}
.filters select,.filters input{{padding:.5rem .85rem;border:1.5px solid var(--gris-bd);
  border-radius:8px;font-size:.88rem;color:var(--texto);background:white;}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:1.5rem;}}
.metric-card{{background:white;border-radius:14px;padding:1.1rem 1.25rem;
  border:1px solid var(--gris-bd);box-shadow:0 1px 4px rgba(0,0,0,.04);}}
.metric-card .val{{font-size:2rem;font-weight:700;color:var(--azul);}}
.metric-card .lbl{{font-size:.8rem;color:var(--texto-2);margin-top:.15rem;}}
.metric-card.alerta .val{{color:var(--rojo);}}
.metric-card.ok .val{{color:var(--verde);}}
.alertas-strip{{background:var(--rojo-bg);border:1px solid #fca5a5;border-radius:12px;
  padding:.85rem 1.25rem;margin-bottom:1.25rem;display:none;}}
.alertas-strip h3{{font-size:.9rem;color:var(--rojo);margin-bottom:.5rem;}}
.alerta-chip{{display:inline-block;background:var(--rojo);color:white;
  padding:.2rem .75rem;border-radius:99px;font-size:.78rem;margin:2px 4px;cursor:pointer;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:1.5rem;}}
.card{{background:white;border-radius:14px;padding:1.25rem;
  border:1px solid var(--gris-bd);box-shadow:0 1px 4px rgba(0,0,0,.04);}}
.card h2{{font-size:.95rem;font-weight:600;color:var(--azul);margin-bottom:1rem;
  border-bottom:1px solid var(--gris-bd);padding-bottom:.5rem;}}
.table-wrap{{overflow-x:auto;}}
table{{width:100%;border-collapse:collapse;font-size:.85rem;}}
thead th{{background:var(--gris-bg);padding:.6rem .9rem;text-align:left;font-weight:600;
  color:var(--texto-2);font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;
  border-bottom:1px solid var(--gris-bd);}}
tbody tr{{border-bottom:1px solid var(--gris-bd);cursor:pointer;transition:background .15s;}}
tbody tr:hover{{background:#f1f5f9;}}
tbody td{{padding:.65rem .9rem;}}
.score-badge{{display:inline-block;padding:2px 10px;border-radius:99px;font-size:.75rem;font-weight:600;}}
.score-alto{{background:var(--rojo-bg);color:var(--rojo);}}
.score-medio{{background:var(--ambar-bg);color:var(--ambar);}}
.score-bajo{{background:var(--verde-bg);color:var(--verde);}}
.inactivo-item{{display:flex;align-items:center;justify-content:space-between;
  padding:.5rem 0;border-bottom:1px solid var(--gris-bd);font-size:.85rem;cursor:pointer;}}
.inactivo-item:last-child{{border:none;}}
.dias-badge{{background:var(--ambar-bg);color:var(--ambar);padding:2px 8px;
  border-radius:99px;font-size:.75rem;font-weight:600;}}
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);
  z-index:100;align-items:center;justify-content:center;}}
.modal-overlay.open{{display:flex;}}
.modal{{background:white;border-radius:20px;padding:2rem;width:560px;
  max-height:85vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3);}}
.modal-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.25rem;}}
.modal-header h2{{font-size:1.2rem;color:var(--azul);}}
.modal-close{{background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--texto-2);}}
.modal-section{{margin-bottom:1rem;}}
.modal-section h3{{font-size:.85rem;font-weight:600;color:var(--texto-2);
  text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem;}}
.concepto-bar{{margin-bottom:.4rem;}}
.concepto-bar-label{{display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:2px;}}
.concepto-bar-bg{{background:var(--gris-bd);border-radius:99px;height:8px;overflow:hidden;}}
.concepto-bar-fill{{height:100%;border-radius:99px;background:var(--azul-med);}}
.concepto-bar-fill.alto{{background:var(--rojo);}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;}}
.info-item{{background:var(--gris-bg);border-radius:8px;padding:.6rem .9rem;}}
.info-item .val{{font-size:1.1rem;font-weight:700;color:var(--azul);}}
.info-item .lbl{{font-size:.75rem;color:var(--texto-2);}}
.update-btn{{background:var(--azul-med);color:white;border:none;padding:.4rem 1rem;
  border-radius:8px;cursor:pointer;font-size:.83rem;margin-left:auto;}}
.update-btn:hover{{opacity:.88;}}
@media(max-width:900px){{.metrics{{grid-template-columns:repeat(2,1fr);}}.grid2{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>

<div class="topbar">
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:1.8rem">🐍</span>
    <div>
      <h1>SOFIA.py — Panel Docente</h1>
      <span>{docente['nombre']} · {docente['cargo']}</span>
    </div>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <button class="update-btn" onclick="actualizarDatos()">↻ Actualizar datos</button>
    <a class="btn-logout" href="/logout">Cerrar sesión</a>
  </div>
</div>

<div class="main">
  <div class="filters">
    <label style="font-size:.85rem;font-weight:500;color:var(--texto-2)">Filtrar:</label>
    <select id="filtro-semestre" onchange="aplicarFiltro()">
      <option value="todos">Todos los semestres</option>
      {opts_sem}
    </select>
    <input type="text" id="filtro-buscar" placeholder="🔍 Buscar estudiante..."
           oninput="aplicarFiltro()" style="min-width:200px">
    <span id="ultima-act" style="margin-left:auto;font-size:.78rem;color:#94a3b8"></span>
  </div>

  <div class="alertas-strip" id="alertas-strip">
    <h3>⚠️ Estudiantes en zona de riesgo (score ≥ 6.5)</h3>
    <div id="alertas-chips"></div>
  </div>

  <div class="metrics">
    <div class="metric-card"><div class="val" id="met-total">—</div>
      <div class="lbl">Estudiantes registrados</div></div>
    <div class="metric-card alerta"><div class="val" id="met-riesgo">—</div>
      <div class="lbl">En zona de riesgo</div></div>
    <div class="metric-card"><div class="val" id="met-prom-score">—</div>
      <div class="lbl">Score promedio del grupo</div></div>
    <div class="metric-card ok"><div class="val" id="met-prom-intentos">—</div>
      <div class="lbl">Intentos promedio</div></div>
  </div>

  <div class="grid2">
    <div class="card"><h2>Errores por concepto</h2>
      <canvas id="chart-errores" height="220"></canvas></div>
    <div class="card"><h2>Distribución de riesgo</h2>
      <canvas id="chart-scores" height="220"></canvas></div>
  </div>

  <div class="card" style="margin-bottom:1rem">
    <h2>Estudiantes — ordenados por score de riesgo</h2>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Nombre</th><th>Semestre</th><th>Score riesgo</th>
          <th>Intentos prom.</th><th>Interacciones</th>
          <th>Dificultades principales</th><th>Última sesión</th><th>Estado</th>
        </tr></thead>
        <tbody id="tabla-body"></tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Estudiantes inactivos (sin actividad en 3+ días)</h2>
    <div id="inactivos-list"></div>
  </div>
</div>

<div class="modal-overlay" id="modal-overlay" onclick="cerrarModal(event)">
  <div class="modal">
    <div class="modal-header">
      <div><h2 id="modal-nombre">—</h2>
        <small id="modal-sub" style="color:#64748b">—</small></div>
      <button class="modal-close" onclick="cerrarModal()">×</button>
    </div>
    <div class="info-grid" id="modal-metricas"></div>
    <div class="modal-section" style="margin-top:1rem">
      <h3>Errores por concepto</h3>
      <div id="modal-barras"></div>
    </div>
    <div class="modal-section">
      <h3>Recomendación pedagógica</h3>
      <div id="modal-rec" style="font-size:.88rem;line-height:1.6;background:#f8fafc;
        border-radius:8px;padding:.75rem;color:#1e293b"></div>
    </div>
  </div>
</div>

<script>
let PERFILES = {perfiles_json};
let chartE = null, chartS = null;

document.getElementById("ultima-act").textContent =
  "Última actualización: " + new Date().toLocaleString("es-CO");

function actualizarDatos() {{
  fetch("/api/perfiles")
    .then(r => r.json())
    .then(data => {{
      PERFILES = data;
      document.getElementById("ultima-act").textContent =
        "Actualizado: " + new Date().toLocaleString("es-CO");
      aplicarFiltro();
    }})
    .catch(() => alert("Error al actualizar. ¿El servidor está corriendo?"));
}}

function filtrados() {{
  const sem    = document.getElementById("filtro-semestre").value;
  const buscar = document.getElementById("filtro-buscar").value.toLowerCase();
  return PERFILES
    .filter(p => sem === "todos" || p.semestre == sem)
    .filter(p => !buscar || p.nombre.toLowerCase().includes(buscar))
    .sort((a,b) => b.score_riesgo - a.score_riesgo);
}}

function aplicarFiltro() {{
  const datos = filtrados();
  renderMetricas(datos);
  renderAlertas(datos);
  renderTabla(datos);
  renderInactivos(datos);
  renderCharts(datos);
}}

function renderMetricas(d) {{
  document.getElementById("met-total").textContent = d.length;
  document.getElementById("met-riesgo").textContent = d.filter(p=>p.en_alerta).length;
  document.getElementById("met-prom-score").textContent = d.length
    ? (d.reduce((a,p)=>a+p.score_riesgo,0)/d.length).toFixed(1) : "—";
  document.getElementById("met-prom-intentos").textContent = d.length
    ? (d.reduce((a,p)=>a+p.intentos_promedio,0)/d.length).toFixed(1) : "—";
}}

function renderAlertas(d) {{
  const en = d.filter(p=>p.en_alerta);
  const s  = document.getElementById("alertas-strip");
  if (!en.length) {{ s.style.display="none"; return; }}
  s.style.display = "block";
  document.getElementById("alertas-chips").innerHTML = en.map(p=>
    `<span class="alerta-chip" onclick="abrirModal('${{p.estudiante_id}}')">
      ⚠ ${{p.nombre}} (${{p.score_riesgo}})</span>`).join("");
}}

function diasDesde(f) {{
  if (!f) return 999;
  return Math.floor((Date.now()-new Date(f).getTime())/86400000);
}}

function estado(dias) {{
  if (dias<=1) return "🟢 Activo";
  if (dias<=3) return `🟡 Hace ${{dias}}d`;
  return `🔴 ${{dias}}d sin actividad`;
}}

function renderTabla(d) {{
  const tb = document.getElementById("tabla-body");
  if (!d.length) {{
    tb.innerHTML=`<tr><td colspan="8" style="text-align:center;padding:2rem;color:#64748b">
      Sin estudiantes para este filtro.</td></tr>`; return;
  }}
  tb.innerHTML = d.map(p => {{
    const dias = diasDesde(p.ultima_sesion);
    const sc   = p.score_riesgo>=6.5?"score-alto":p.score_riesgo>=4?"score-medio":"score-bajo";
    const conc = (p.errores_frecuentes||[]).slice(0,2)
      .map(c=>`<code style="font-size:.75rem;background:#f1f5f9;padding:1px 5px;border-radius:4px">${{c}}</code>`).join(" ");
    return `<tr onclick="abrirModal('${{p.estudiante_id}}')">
      <td><strong>${{p.nombre}}</strong></td>
      <td>Sem. ${{p.semestre}}</td>
      <td><span class="score-badge ${{sc}}">${{p.score_riesgo}}</span></td>
      <td>${{p.intentos_promedio}}</td>
      <td>${{p.interacciones}}</td>
      <td>${{conc||"—"}}</td>
      <td style="font-size:.8rem;color:#64748b">${{p.ultima_sesion||"—"}}</td>
      <td style="font-size:.82rem">${{estado(dias)}}</td>
    </tr>`;
  }}).join("");
}}

function renderInactivos(d) {{
  const in3 = d.filter(p=>diasDesde(p.ultima_sesion)>=3)
               .sort((a,b)=>diasDesde(b.ultima_sesion)-diasDesde(a.ultima_sesion));
  const c = document.getElementById("inactivos-list");
  if (!in3.length) {{
    c.innerHTML=`<p style="color:#64748b;font-size:.88rem">✅ Todos con actividad reciente.</p>`; return;
  }}
  c.innerHTML = in3.map(p=>{{
    const d2=diasDesde(p.ultima_sesion);
    return `<div class="inactivo-item" onclick="abrirModal('${{p.estudiante_id}}')">
      <span><strong>${{p.nombre}}</strong>
        <span style="color:#64748b;font-size:.8rem"> · Sem. ${{p.semestre}}</span></span>
      <span class="dias-badge">${{d2}} días sin actividad</span></div>`;
  }}).join("");
}}

function renderCharts(d) {{
  const em={{}};
  d.forEach(p=>Object.entries(p.errores_por_concepto||{{}}).forEach(([c,n])=>em[c]=(em[c]||0)+n));
  const el=Object.keys(em).sort((a,b)=>em[b]-em[a]);
  const ev=el.map(c=>em[c]);
  const cols=["#6366f1","#3b82f6","#06b6d4","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899"];
  if(chartE) chartE.destroy();
  chartE=new Chart(document.getElementById("chart-errores"),{{
    type:"bar",data:{{labels:el,datasets:[{{label:"Errores",data:ev,
      backgroundColor:el.map((_,i)=>cols[i%8]),borderRadius:6}}]}},
    options:{{responsive:true,plugins:{{legend:{{display:false}}}},
      scales:{{y:{{beginAtZero:true,ticks:{{stepSize:1}}}}}}}}
  }});
  const bajo=d.filter(p=>p.score_riesgo<4).length;
  const medio=d.filter(p=>p.score_riesgo>=4&&p.score_riesgo<6.5).length;
  const alto=d.filter(p=>p.score_riesgo>=6.5).length;
  if(chartS) chartS.destroy();
  chartS=new Chart(document.getElementById("chart-scores"),{{
    type:"doughnut",data:{{labels:["Bajo (<4)","Medio (4-6.5)","Alto (≥6.5)"],
      datasets:[{{data:[bajo,medio,alto],
        backgroundColor:["#dcfce7","#fef9c3","#fee2e2"],
        borderColor:["#166534","#854d0e","#991b1b"],borderWidth:2}}]}},
    options:{{responsive:true,plugins:{{legend:{{position:"bottom",
      labels:{{font:{{size:11}}}}}}}}}}
  }});
}}

function abrirModal(id) {{
  const p=PERFILES.find(x=>x.estudiante_id===id); if(!p) return;
  document.getElementById("modal-nombre").textContent=p.nombre;
  document.getElementById("modal-sub").textContent=
    `Semestre ${{p.semestre}} · ${{p.interacciones}} interacciones · Última sesión: ${{p.ultima_sesion}}`;
  const sc=p.score_riesgo>=6.5?"#991b1b":p.score_riesgo>=4?"#854d0e":"#166534";
  document.getElementById("modal-metricas").innerHTML=`
    <div class="info-item"><div class="val" style="color:${{sc}}">${{p.score_riesgo}}</div>
      <div class="lbl">Score riesgo</div></div>
    <div class="info-item"><div class="val">${{p.intentos_promedio}}</div>
      <div class="lbl">Intentos promedio</div></div>
    <div class="info-item"><div class="val">${{p.interacciones}}</div>
      <div class="lbl">Interacciones</div></div>
    <div class="info-item"><div class="val">${{diasDesde(p.ultima_sesion)}}d</div>
      <div class="lbl">Días sin actividad</div></div>`;
  const errs=Object.entries(p.errores_por_concepto||{{}}).sort((a,b)=>b[1]-a[1]);
  const mx=errs[0]?.[1]||1;
  document.getElementById("modal-barras").innerHTML=errs.map(([c,n])=>`
    <div class="concepto-bar">
      <div class="concepto-bar-label"><span>${{c.replace(/_/g," ")}}</span><span>${{n}} error(es)</span></div>
      <div class="concepto-bar-bg"><div class="concepto-bar-fill ${{n>=mx?"alto":""}}"
        style="width:${{Math.round(n/mx*100)}}%"></div></div>
    </div>`).join("")||"<p style='color:#64748b;font-size:.85rem'>Sin errores registrados.</p>";
  const recs={{
    ciclos:"Reforzar condición de parada en while y valor final de range(). Ejercicios de contadores.",
    funciones:"Trabajar diferencia print vs return con ejemplos donde el resultado se usa en otra operación.",
    listas:"Practicar indexación. Recordar que índices van de 0 a len-1. Ejercicios de IndexError intencional.",
    recursion:"Sesión dedicada al caso base. Dibujar árbol de llamadas en papel antes de codificar.",
    strings:"Métodos de string con ejercicios de texto. Practicar f-strings y slicing [::-1].",
    condicionales:"Revisar == vs = y estructura if-elif-else con múltiples condiciones.",
    diccionarios:"Acceso seguro con get(). Ejercicios de frecuencia de palabras.",
    variables_y_tipos:"Conversión de tipos y TypeError. Ejercicios que combinen int, str y float.",
  }};
  const top=(p.errores_frecuentes||[])[0];
  const alerta=p.en_alerta?`<p style="color:#991b1b;font-weight:600;margin-bottom:.5rem">
    ⚠️ Estudiante en zona de alto riesgo. Se recomienda contacto directo.</p>`:"";
  document.getElementById("modal-rec").innerHTML=alerta+(top
    ?`<p>Principal dificultad: <strong>${{top.replace(/_/g," ")}}</strong></p>
       <p style="margin-top:.4rem">${{recs[top]||"Revisar fundamentos del concepto."}}</p>`
    :"✅ Buen desempeño general. Proponer ejercicios de nivel intermedio.");
  document.getElementById("modal-overlay").classList.add("open");
}}

function cerrarModal(e) {{
  if(!e||e.target===document.getElementById("modal-overlay"))
    document.getElementById("modal-overlay").classList.remove("open");
}}

aplicarFiltro();
</script>
</body>
</html>"""


# ══ SERVIDOR HTTP ══════════════════════════════════════════════════════════
class DashboardHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Silenciar logs del servidor

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        # Login page
        if path in ("/", "/login"):
            self.enviar_login()

        # API perfiles (AJAX)
        elif path == "/api/perfiles":
            sesion = self.obtener_sesion()
            if not sesion:
                self.enviar_json({"error": "no autorizado"}, 401)
                return
            docente  = cargar_docentes().get(sesion)
            perfiles = cargar_perfiles(docente.get("semestres") if docente else None)
            self.enviar_json(perfiles)

        # Dashboard
        elif path == "/dashboard":
            sesion = self.obtener_sesion()
            if not sesion:
                self.redirect("/")
                return
            docente = cargar_docentes().get(sesion)
            if not docente:
                self.redirect("/")
                return
            html = html_dashboard(docente)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        # Logout
        elif path == "/logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "sesion=; Max-Age=0; Path=/")
            self.send_header("Location", "/")
            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/login":
            length  = int(self.headers.get("Content-Length", 0))
            body    = self.rfile.read(length).decode("utf-8")
            params  = dict(urllib.parse.parse_qsl(body))
            usuario = params.get("usuario", "").strip().lower()
            pwd     = params.get("password", "")
            docente = verificar_credenciales(usuario, pwd)
            if docente:
                self.send_response(302)
                self.send_header("Set-Cookie", f"sesion={usuario}; Path=/; HttpOnly")
                self.send_header("Location", "/dashboard")
                self.end_headers()
            else:
                self.enviar_login(error=True)
        else:
            self.send_response(404)
            self.end_headers()

    def obtener_sesion(self):
        cookies = self.headers.get("Cookie", "")
        for c in cookies.split(";"):
            c = c.strip()
            if c.startswith("sesion="):
                return c[7:].strip() or None
        return None

    def redirect(self, url):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def enviar_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def enviar_login(self, error=False):
        error_html = '<p style="color:#991b1b;font-size:.85rem;text-align:center;margin-top:.5rem">Usuario o contraseña incorrectos.</p>' if error else ""
        html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SOFIA.py — Login Docente</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;
  justify-content:center;background:linear-gradient(135deg,#1a1a2e 0%,#0f3460 100%);}}
.card{{background:white;border-radius:20px;padding:2.5rem 2rem;width:380px;
  box-shadow:0 20px 60px rgba(0,0,0,.3);}}
.logo{{text-align:center;font-size:3rem;margin-bottom:.5rem;}}
.title{{text-align:center;font-size:1.5rem;font-weight:700;color:#1e3a5f;margin-bottom:.25rem;}}
.sub{{text-align:center;color:#64748b;font-size:.85rem;margin-bottom:1.75rem;}}
.fg{{margin-bottom:1rem;}}
.fg label{{font-size:.85rem;font-weight:500;color:#64748b;display:block;margin-bottom:.35rem;}}
.fg input{{width:100%;padding:.7rem 1rem;border:1.5px solid #e2e8f0;border-radius:10px;
  font-size:.95rem;color:#1e293b;}}
.fg input:focus{{outline:none;border-color:#2563eb;}}
.btn{{width:100%;padding:.8rem;background:#1e3a5f;color:white;border:none;
  border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;margin-top:.5rem;}}
.btn:hover{{opacity:.88;}}
</style></head>
<body><div class="card">
  <div class="logo">🐍</div>
  <div class="title">SOFIA.py</div>
  <div class="sub">Panel de Control Docente · UPTC</div>
  <form method="POST" action="/login">
    <div class="fg"><label>Usuario</label>
      <input name="usuario" placeholder="ej: msuarez" autocomplete="username" required></div>
    <div class="fg"><label>Contraseña</label>
      <input name="password" type="password" placeholder="••••••••" required></div>
    <button class="btn" type="submit">Ingresar →</button>
  </form>
  {error_html}
</div></body></html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    import socket
    print(f"\n🐍 SOFIA.py — Servidor Dashboard")
    print(f"{'─'*40}")
    print(f"  URL     : http://localhost:{PORT}")
    print(f"  Perfiles: {DIR_PERFILES}")
    print(f"  Docentes: {DOCENTES_JSON}")
    print(f"{'─'*40}")
    print(f"  msuarez / uptc2025  → todos los semestres")
    print(f"  frincon / prog2025  → semestres 1, 2, 3")
    print(f"{'─'*40}")
    print(f"  Presiona Ctrl+C para detener\n")

    server = http.server.HTTPServer(("", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")
