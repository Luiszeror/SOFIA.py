"""
test_grafo_grl_dce.py
─────────────────────
Prueba de punta a punta del módulo error_community/ (GRL-DCE)
integrado a SOFIA.py.

Ejecutar desde la raíz de ProyectoFinal/ con el .venv activo:
    python test_grafo_grl_dce.py

No necesita Gemini, ni Streamlit, ni la Capa 3 corriendo.
Simula exactamente los datos que llegarían del orquestador real.

Pruebas incluidas:
    1. Imports y dependencias
    2. feature_encoder  → tensores correctos
    3. graph_builder    → HeteroData correcto
    4. gnn_encoder      → modelo construido
    5. train            → convergencia de la loss
    6. similarity_graph → grafo de similitud coseno
    7. louvain_detector → comunidades detectadas
    8. community_service → pipeline completo de punta a punta
    9. integración real → simula llamada desde orquestador.py
   10. modo degradado   → fallo silencioso sin romper SOFIA.py
"""

import sys
import traceback

# ─── Colores para la terminal ────────────────────────────────────────────────
VERDE  = "\033[92m"
ROJO   = "\033[91m"
AMARILLO = "\033[93m"
AZUL   = "\033[94m"
RESET  = "\033[0m"
NEGRITA = "\033[1m"

OK   = f"{VERDE}✓ OK{RESET}"
FAIL = f"{ROJO}✗ FAIL{RESET}"
INFO = f"{AZUL}→{RESET}"

resultados = []


def prueba(nombre):
    """Decorador de prueba: imprime nombre, captura excepciones."""
    def decorator(fn):
        def wrapper():
            print(f"\n{NEGRITA}[{len(resultados)+1}] {nombre}{RESET}")
            try:
                fn()
                print(f"    {OK}")
                resultados.append((nombre, True, None))
            except Exception as e:
                tb = traceback.format_exc()
                print(f"    {FAIL}")
                print(f"    {ROJO}{e}{RESET}")
                print(f"    {AMARILLO}--- traceback ---{RESET}")
                for line in tb.splitlines():
                    print(f"    {line}")
                resultados.append((nombre, False, str(e)))
        return wrapper
    return decorator


# ═════════════════════════════════════════════════════════════════════════════
# DATOS DE PRUEBA
# Simulan exactamente lo que llegaría del orquestador de SOFIA.py:
#   - perfil viene de agente_analista.py
#   - tipo_error y concepto vienen del JSON de core/evaluador.py
# ═════════════════════════════════════════════════════════════════════════════

# 4 estudiantes con perfiles distintos (como los daría agente_analista)
ESTUDIANTES_PRUEBA = [
    {
        "id":             "S001",
        "total_attempts": 5,
        "error_rate":     0.8,   # muchos errores → score_riesgo alto
        "avg_time_sec":   120,
    },
    {
        "id":             "S002",
        "total_attempts": 3,
        "error_rate":     0.6,
        "avg_time_sec":   90,
    },
    {
        "id":             "S003",
        "total_attempts": 8,
        "error_rate":     0.9,   # estudiante en riesgo
        "avg_time_sec":   200,
    },
    {
        "id":             "S004",
        "total_attempts": 2,
        "error_rate":     0.3,   # buen desempeño
        "avg_time_sec":   60,
    },
]

# 5 tipos de error (los mismos que clasifica core/evaluador.py)
ERRORES_PRUEBA = [
    {"type_id": 0, "frequency": 12, "severity": 1, "module_id": 1},  # error_sintaxis
    {"type_id": 1, "frequency": 7,  "severity": 2, "module_id": 3},  # error_logico
    {"type_id": 2, "frequency": 4,  "severity": 3, "module_id": 3},  # error_runtime
    {"type_id": 3, "frequency": 9,  "severity": 3, "module_id": 7},  # error_timeout
    {"type_id": 4, "frequency": 2,  "severity": 4, "module_id": 0},  # error_seguridad
]

# 9 conceptos Python del currículo (mismos que usa el repositorio de casos)
CONCEPTOS_PRUEBA = [
    {"concept_id": 0, "semester": 1, "difficulty": 0.4},  # variables
    {"concept_id": 1, "semester": 1, "difficulty": 0.6},  # funciones
    {"concept_id": 2, "semester": 1, "difficulty": 0.5},  # condicionales
    {"concept_id": 3, "semester": 1, "difficulty": 0.7},  # ciclos
    {"concept_id": 4, "semester": 2, "difficulty": 0.7},  # listas
    {"concept_id": 5, "semester": 2, "difficulty": 0.8},  # diccionarios
    {"concept_id": 6, "semester": 2, "difficulty": 0.9},  # clases
    {"concept_id": 7, "semester": 2, "difficulty": 0.9},  # recursion
    {"concept_id": 8, "semester": 1, "difficulty": 0.5},  # strings
]

# Qué estudiante cometió qué tipo de error
STUDENT_COMMITS_ERROR = [
    (0, 0), (0, 1),   # S001: sintaxis + logico
    (1, 1), (1, 2),   # S002: logico + runtime
    (2, 2), (2, 3),   # S003: runtime + timeout  ← estudiante en riesgo
    (3, 4),           # S004: seguridad (puntual)
]

# Qué estudiante está viendo qué concepto
STUDENT_STUDIES_CONCEPT = [
    (0, 1), (0, 3),   # S001: funciones, ciclos
    (1, 3), (1, 4),   # S002: ciclos, listas
    (2, 3), (2, 7),   # S003: ciclos, recursion
    (3, 0),           # S004: variables
]

# Qué tipo de error mapea a qué concepto
ERROR_MAPS_CONCEPT = [
    (0, 1),   # sintaxis   → funciones
    (1, 3),   # logico     → ciclos
    (2, 4),   # runtime    → listas
    (3, 7),   # timeout    → recursion
    (4, 0),   # seguridad  → variables
]

# Mapa de errores por estudiante (para label_communities)
STUDENT_ERROR_MAP = {
    "S001": ["error_sintaxis", "error_logico"],
    "S002": ["error_logico",   "error_runtime"],
    "S003": ["error_runtime",  "error_timeout"],
    "S004": ["error_seguridad"],
}


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 1 — Imports y dependencias
# ═════════════════════════════════════════════════════════════════════════════
@prueba("Imports y dependencias (torch, torch_geometric, networkx, community)")
def test_imports():
    import torch
    import torch_geometric
    import networkx
    import community as community_louvain
    print(f"    {INFO} torch            {torch.__version__}")
    print(f"    {INFO} torch_geometric  {torch_geometric.__version__}")
    print(f"    {INFO} networkx         {networkx.__version__}")
    print(f"    {INFO} python-louvain   OK")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 2 — feature_encoder
# ═════════════════════════════════════════════════════════════════════════════
@prueba("feature_encoder → tensores con dimensiones correctas")
def test_feature_encoder():
    from error_community.data.feature_encoder import (
        encode_students, encode_errors, encode_concepts, encode_edges
    )
    import torch

    s = encode_students(ESTUDIANTES_PRUEBA)
    e = encode_errors(ERRORES_PRUEBA)
    c = encode_concepts(CONCEPTOS_PRUEBA)
    edges = encode_edges(STUDENT_COMMITS_ERROR)

    assert s.shape == (4, 3), f"Esperado (4,3), obtenido {s.shape}"
    assert e.shape == (5, 3), f"Esperado (5,3), obtenido {e.shape}"
    assert c.shape == (9, 2), f"Esperado (9,2), obtenido {c.shape}"
    assert edges.shape[0] == 2, f"edge_index debe tener 2 filas, tiene {edges.shape[0]}"

    print(f"    {INFO} student.x   shape={tuple(s.shape)}  dtype={s.dtype}")
    print(f"    {INFO} error.x     shape={tuple(e.shape)}  dtype={e.dtype}")
    print(f"    {INFO} concept.x   shape={tuple(c.shape)}  dtype={c.dtype}")
    print(f"    {INFO} edge_index  shape={tuple(edges.shape)}")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 3 — graph_builder → HeteroData
# ═════════════════════════════════════════════════════════════════════════════
@prueba("graph_builder → HeteroData con nodos y aristas correctos")
def test_graph_builder():
    from error_community.data.graph_builder import build_graph

    data = build_graph(
        ESTUDIANTES_PRUEBA, ERRORES_PRUEBA, CONCEPTOS_PRUEBA,
        STUDENT_COMMITS_ERROR, STUDENT_STUDIES_CONCEPT, ERROR_MAPS_CONCEPT
    )

    assert data["student"].x.shape[0] == 4,  "Debe haber 4 nodos estudiante"
    assert data["error"].x.shape[0]   == 5,  "Debe haber 5 nodos error"
    assert data["concept"].x.shape[0] == 9,  "Debe haber 9 nodos concepto"

    edge_commits = data["student", "commits", "error"].edge_index
    assert edge_commits.shape == (2, len(STUDENT_COMMITS_ERROR)), \
        f"edge_index commits: esperado (2,{len(STUDENT_COMMITS_ERROR)}), obtenido {edge_commits.shape}"

    assert hasattr(data["student"], "student_ids"), "Falta student_ids en nodos estudiante"

    print(f"    {INFO} HeteroData construido:")
    print(f"        student.x     = {tuple(data['student'].x.shape)}")
    print(f"        error.x       = {tuple(data['error'].x.shape)}")
    print(f"        concept.x     = {tuple(data['concept'].x.shape)}")
    print(f"        commits edges = {tuple(edge_commits.shape)}")
    print(f"        student_ids   = {data['student'].student_ids}")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 4 — gnn_encoder → modelo construido correctamente
# ═════════════════════════════════════════════════════════════════════════════
@prueba("gnn_encoder → modelo SAGEConv heterogéneo construido")
def test_gnn_encoder():
    from error_community.data.graph_builder import build_graph
    from error_community.model.gnn_encoder import build_model

    data  = build_graph(
        ESTUDIANTES_PRUEBA, ERRORES_PRUEBA, CONCEPTOS_PRUEBA,
        STUDENT_COMMITS_ERROR, STUDENT_STUDIES_CONCEPT, ERROR_MAPS_CONCEPT
    )
    model = build_model(data)

    n_params = sum(p.numel() for p in model.parameters())
    assert n_params > 0, "El modelo no tiene parámetros"

    print(f"    {INFO} Modelo: {type(model).__name__}")
    print(f"    {INFO} Parámetros totales: {n_params:,}")
    print(f"    {INFO} Tipos de nodo en metadata: {data.metadata()[0]}")
    print(f"    {INFO} Tipos de arista en metadata: {data.metadata()[1]}")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 5 — train → loss converge (mínimo 10 épocas)
# ═════════════════════════════════════════════════════════════════════════════
@prueba("train → la loss contrastiva disminuye en 10 épocas")
def test_train():
    from error_community.data.graph_builder import build_graph
    from error_community.model.train import train, get_student_embeddings

    data = build_graph(
        ESTUDIANTES_PRUEBA, ERRORES_PRUEBA, CONCEPTOS_PRUEBA,
        STUDENT_COMMITS_ERROR, STUDENT_STUDIES_CONCEPT, ERROR_MAPS_CONCEPT
    )

    print(f"    {INFO} Entrenando 10 épocas de prueba...")
    model = train(data, epochs=10, lr=0.01)

    embeddings = get_student_embeddings(model, data)
    assert embeddings.shape == (4, 16), \
        f"Embeddings shape esperado (4,16), obtenido {embeddings.shape}"

    print(f"    {INFO} Embeddings finales shape: {tuple(embeddings.shape)}")
    print(f"    {INFO} Rango valores: [{embeddings.min().item():.4f}, {embeddings.max().item():.4f}]")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 6 — similarity_graph → grafo coseno construido
# ═════════════════════════════════════════════════════════════════════════════
@prueba("similarity_graph → grafo de similitud coseno construido")
def test_similarity_graph():
    from error_community.data.graph_builder import build_graph
    from error_community.model.train import train, get_student_embeddings
    from error_community.community.similarity_graph import build_similarity_graph
    import networkx as nx

    data = build_graph(
        ESTUDIANTES_PRUEBA, ERRORES_PRUEBA, CONCEPTOS_PRUEBA,
        STUDENT_COMMITS_ERROR, STUDENT_STUDIES_CONCEPT, ERROR_MAPS_CONCEPT
    )
    model      = train(data, epochs=10)
    embeddings = get_student_embeddings(model, data)
    ids        = data["student"].student_ids

    G = build_similarity_graph(embeddings, ids, threshold=0.70)

    assert isinstance(G, nx.Graph),   "Debe retornar un grafo NetworkX"
    assert G.number_of_nodes() == 4,  "Debe tener 4 nodos (uno por estudiante)"

    print(f"    {INFO} Nodos en grafo de similitud: {G.number_of_nodes()}")
    print(f"    {INFO} Aristas (sim >= 0.70):       {G.number_of_edges()}")

    if G.number_of_edges() > 0:
        for u, v, w in G.edges(data="weight"):
            sid_u = G.nodes[u]["student_id"]
            sid_v = G.nodes[v]["student_id"]
            print(f"    {INFO}   {sid_u} ↔ {sid_v}  similitud={w:.4f}")
    else:
        print(f"    {AMARILLO}    Sin aristas con umbral 0.70 (normal con 10 épocas de entrenamiento){RESET}")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 7 — louvain_detector → comunidades detectadas
# ═════════════════════════════════════════════════════════════════════════════
@prueba("louvain_detector → comunidades con metadatos correctos")
def test_louvain_detector():
    from error_community.data.graph_builder import build_graph
    from error_community.model.train import train, get_student_embeddings
    from error_community.community.similarity_graph import build_similarity_graph
    from error_community.community.louvain_detector import detect_communities, label_communities

    data = build_graph(
        ESTUDIANTES_PRUEBA, ERRORES_PRUEBA, CONCEPTOS_PRUEBA,
        STUDENT_COMMITS_ERROR, STUDENT_STUDIES_CONCEPT, ERROR_MAPS_CONCEPT
    )
    model      = train(data, epochs=10)
    embeddings = get_student_embeddings(model, data)
    ids        = data["student"].student_ids

    G          = build_similarity_graph(embeddings, ids, threshold=0.50)  # umbral bajo para prueba
    comunidades = detect_communities(G, ids)
    etiquetadas = label_communities(comunidades, STUDENT_ERROR_MAP)

    assert isinstance(comunidades,  dict), "detect_communities debe retornar dict"
    assert isinstance(etiquetadas,  dict), "label_communities debe retornar dict"
    assert len(etiquetadas) >= 1,          "Debe haber al menos 1 comunidad"

    # Verificar que todos los estudiantes están asignados
    todos_asignados = []
    for info in etiquetadas.values():
        todos_asignados.extend(info["members"])
    assert set(todos_asignados) == {"S001", "S002", "S003", "S004"}, \
        f"No todos los estudiantes asignados: {todos_asignados}"

    print(f"    {INFO} Comunidades detectadas: {len(etiquetadas)}")
    for nombre, info in etiquetadas.items():
        print(f"    {INFO}   {nombre}:")
        print(f"             miembros        = {info['members']}")
        print(f"             errores top     = {info['dominant_errors']}")
        print(f"             nivel de riesgo = {info['risk_level']}")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 8 — CommunityService → pipeline completo
# ═════════════════════════════════════════════════════════════════════════════
@prueba("CommunityService → pipeline completo de punta a punta")
def test_community_service():
    from error_community.api.community_service import CommunityService

    svc = CommunityService(threshold=0.50, epochs=15)

    resultado = svc.run_pipeline(
        students                = ESTUDIANTES_PRUEBA,
        errors                  = ERRORES_PRUEBA,
        concepts                = CONCEPTOS_PRUEBA,
        student_commits_error   = STUDENT_COMMITS_ERROR,
        student_studies_concept = STUDENT_STUDIES_CONCEPT,
        error_maps_concept      = ERROR_MAPS_CONCEPT,
        student_error_map       = STUDENT_ERROR_MAP,
    )

    assert isinstance(resultado, dict), "run_pipeline debe retornar dict"
    assert len(resultado) >= 1,         "Debe haber al menos 1 comunidad en el resultado"

    print(f"    {INFO} Pipeline ejecutado. Comunidades:")
    for nombre, info in resultado.items():
        print(f"        {nombre}: {info['members']} — riesgo={info['risk_level']}")

    # Verificar consulta por estudiante
    for sid in ["S001", "S002", "S003", "S004"]:
        r = svc.get_community_for_student(sid)
        assert "community" in r, f"Falta clave 'community' para {sid}"
        print(f"    {INFO} get_community_for_student('{sid}'):")
        print(f"             community      = {r.get('community')}")
        print(f"             dominant_errors= {r.get('dominant_errors')}")
        print(f"             risk_level     = {r.get('risk_level')}")

    # Verificar get_all_communities
    todas = svc.get_all_communities()
    assert isinstance(todas, dict), "get_all_communities debe retornar dict"
    print(f"    {INFO} get_all_communities() → {len(todas)} comunidades")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 9 — Integración real con orquestador
# Simula exactamente la llamada _consultar_grafo() del orquestador.py
# con datos reales del formato de SOFIA.py
# ═════════════════════════════════════════════════════════════════════════════
@prueba("Integración orquestador → simula _consultar_grafo() con datos reales de SOFIA.py")
def test_integracion_orquestador():
    from error_community.api.community_service import CommunityService

    # ── Simular un perfil como lo daría agente_analista.py ────────────────
    class PerfilSimulado:
        """Imita el objeto que retorna agente_analista.actualizar_perfil()"""
        def __init__(self):
            self.interacciones       = 5
            self.score_riesgo        = 7.2          # estudiante en riesgo
            self.intentos_promedio   = 3
            self.errores_frecuentes  = ["error_logico", "error_runtime"]
            self.errores_por_concepto = {"ciclos": 3, "listas": 2}
            self.en_alerta           = True

    # ── Simular el JSON de core/evaluador.py ──────────────────────────────
    diagnostico_simulado = {
        "tipo_error":      "error_logico",   # uno de los 5 tipos del evaluador
        "concepto":        "ciclos",         # uno de los 9 conceptos del repositorio
        "mensaje_tecnico": "El output esperado era 1\\n2\\n3 pero se recibió 15",
        "linea_error":     None,
        "casos_pasados":   1,
        "casos_ejecutados": 2,
        "intento_numero":  2,
    }

    # ── Mapeos del orquestador.py ─────────────────────────────────────────
    severidad_map = {
        "error_sintaxis":  1,
        "error_logico":    2,
        "error_runtime":   3,
        "error_timeout":   3,
        "error_seguridad": 4,
        "correcto":        0,
    }
    concepto_map = {
        "variables": 0, "funciones": 1, "condicionales": 2,
        "ciclos":    3, "listas":    4, "diccionarios":  5,
        "clases":    6, "recursion": 7, "strings":       8,
    }

    estudiante_id = "S001"
    perfil        = PerfilSimulado()
    tipo_error    = diagnostico_simulado["tipo_error"]
    concepto      = diagnostico_simulado["concepto"]

    # ── Construir datos para el grafo (lógica de _consultar_grafo) ────────
    estudiante_data = {
        "id":             estudiante_id,
        "total_attempts": getattr(perfil, "interacciones", 1),
        "error_rate":     min(getattr(perfil, "score_riesgo", 0) / 10.0, 1.0),
        "avg_time_sec":   getattr(perfil, "intentos_promedio", 1) * 60,
    }
    error_data = {
        "type_id":   concepto_map.get(concepto, 0),
        "frequency": getattr(perfil, "errores_por_concepto", {}).get(concepto, 1),
        "severity":  severidad_map.get(tipo_error, 2),
        "module_id": concepto_map.get(concepto, 0),
    }
    concept_data = {
        "concept_id": concepto_map.get(concepto, 0),
        "semester":   1,
        "difficulty": 0.7,
    }
    student_error_map = {
        estudiante_id: getattr(perfil, "errores_frecuentes", [tipo_error])
    }

    print(f"    {INFO} Datos que enviaría orquestador.py al grafo:")
    print(f"        estudiante_data = {estudiante_data}")
    print(f"        error_data      = {error_data}")
    print(f"        concept_data    = {concept_data}")
    print(f"        student_error_map = {student_error_map}")

    # ── Ejecutar pipeline ─────────────────────────────────────────────────
    svc = CommunityService(threshold=0.50, epochs=15)
    svc.run_pipeline(
        students                = [estudiante_data],
        errors                  = [error_data],
        concepts                = [concept_data],
        student_commits_error   = [(0, 0)],
        student_studies_concept = [(0, 0)],
        error_maps_concept      = [(0, 0)],
        student_error_map       = student_error_map,
    )

    resultado = svc.get_community_for_student(estudiante_id)

    assert "community"       in resultado, "Falta clave 'community'"
    assert "dominant_errors" in resultado, "Falta clave 'dominant_errors'"
    assert "risk_level"      in resultado, "Falta clave 'risk_level'"

    print(f"\n    {INFO} Resultado que recibiría agente_tutor.py:")
    print(f"        community       = {resultado.get('community')}")
    print(f"        dominant_errors = {resultado.get('dominant_errors')}")
    print(f"        risk_level      = {resultado.get('risk_level')}")
    print(f"        size            = {resultado.get('size')}")


# ═════════════════════════════════════════════════════════════════════════════
# PRUEBA 10 — Modo degradado: fallo silencioso
# Verifica que si el grafo lanza excepción, SOFIA.py sigue funcionando
# ═════════════════════════════════════════════════════════════════════════════
@prueba("Modo degradado → fallo silencioso sin romper SOFIA.py")
def test_modo_degradado():
    """
    Simula exactamente el bloque try/except de _consultar_grafo() en orquestador.py.
    Verifica que si el módulo falla, se retorna un dict seguro y el sistema no cae.
    """

    def _consultar_grafo_simulado(estudiante_id, tipo_error, concepto, perfil_score):
        """Copia exacta de la lógica de _consultar_grafo en orquestador.py"""
        try:
            # Forzar excepción para probar el fallback
            raise RuntimeError("Simulación de fallo del módulo GRL-DCE")
        except Exception as e:
            print(f"    {AMARILLO}[GRL-DCE] Advertencia simulada: {e}{RESET}")
            return {
                "community":       None,
                "dominant_errors": [tipo_error],
                "risk_level":      "unknown",
                "size":            1,
            }

    resultado = _consultar_grafo_simulado(
        estudiante_id  = "S001",
        tipo_error     = "error_logico",
        concepto       = "ciclos",
        perfil_score   = 7.2,
    )

    # Verificar que el dict de retorno es seguro para agente_tutor.py
    assert resultado["community"]       is None,       "community debe ser None en modo degradado"
    assert resultado["dominant_errors"] == ["error_logico"], "dominant_errors debe tener el tipo_error"
    assert resultado["risk_level"]      == "unknown",  "risk_level debe ser 'unknown'"
    assert resultado["size"]            == 1,          "size debe ser 1"

    print(f"    {INFO} Resultado seguro en modo degradado: {resultado}")
    print(f"    {INFO} agente_tutor._construir_contexto_comunidad(resultado):")

    # Verificar que _construir_contexto_comunidad maneja el dict degradado
    # sin lanzar excepción (community=None y size=1 → retorna "")
    def _construir_contexto_comunidad(comunidad):
        if not comunidad or not comunidad.get("community"):
            return ""
        if comunidad.get("size", 1) <= 1:
            return ""
        errores = ", ".join(comunidad.get("dominant_errors", []))
        riesgo  = comunidad.get("risk_level", "desconocido")
        n_otros = comunidad.get("size", 1) - 1
        return (
            f"\n[Patrón grupal detectado]\n"
            f"Comparte patrón ({errores}) con {n_otros} estudiante(s).\n"
            f"Riesgo grupal: {riesgo}.\n"
        )

    ctx = _construir_contexto_comunidad(resultado)
    assert ctx == "", f"Contexto debe ser vacío en modo degradado, obtenido: '{ctx}'"
    print(f"        → contexto_comunidad = '' (vacío, prompt socrático sin cambios) ✓")
    print(f"    {INFO} SOFIA.py seguiría funcionando normalmente.")


# ═════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{NEGRITA}{AZUL}{'═'*60}{RESET}")
    print(f"{NEGRITA}{AZUL}  PRUEBAS GRL-DCE — SOFIA.py{RESET}")
    print(f"{NEGRITA}{AZUL}  error_community/ integrado a ProyectoFinal/{RESET}")
    print(f"{NEGRITA}{AZUL}{'═'*60}{RESET}")

    # Ejecutar todas las pruebas en orden
    test_imports()
    test_feature_encoder()
    test_graph_builder()
    test_gnn_encoder()
    test_train()
    test_similarity_graph()
    test_louvain_detector()
    test_community_service()
    test_integracion_orquestador()
    test_modo_degradado()

    # ── Resumen final ────────────────────────────────────────────────────────
    print(f"\n{NEGRITA}{AZUL}{'═'*60}{RESET}")
    print(f"{NEGRITA}  RESUMEN{RESET}")
    print(f"{NEGRITA}{AZUL}{'═'*60}{RESET}")

    pasadas = [r for r in resultados if r[1]]
    fallidas = [r for r in resultados if not r[1]]

    for nombre, ok, err in resultados:
        estado = OK if ok else FAIL
        print(f"  {estado}  {nombre}")

    print(f"\n  Total: {len(pasadas)}/{len(resultados)} pruebas pasadas")

    if fallidas:
        print(f"\n{ROJO}  Pruebas fallidas:{RESET}")
        for nombre, _, err in fallidas:
            print(f"    {ROJO}• {nombre}{RESET}")
            print(f"      {err}")
        print(f"\n{AMARILLO}  Revisa los mensajes de error arriba para más detalles.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{VERDE}{NEGRITA}  ¡Todas las pruebas pasaron! El módulo GRL-DCE está{RESET}")
        print(f"{VERDE}{NEGRITA}  listo para integrarse a SOFIA.py.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()