"""
test_capa2.py — Prueba rápida del Retriever RAG
Ejecutar desde ProyectoFinal/: python test_capa2.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from capa2.retriever.retriever_rag import RetrieverRAG

VERDE  = "\033[92m"
ROJO   = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ── Inicializar el retriever ──────────────────────────────────────────────
print(f"\n{BOLD}CAPA 2 — Test del Retriever RAG{RESET}")
print(f"{DIM}{'─'*50}{RESET}")

retriever = RetrieverRAG(
    directorio_db = os.path.join(os.path.dirname(__file__), "data", "chroma_db"),
    top_k         = 3,
    score_minimo  = 0.1,
)

# ── Queries de prueba — una por concepto ─────────────────────────────────
QUERIES = [
    ("¿Cómo funciona el ciclo for con range?",           "ciclos"),
    ("¿Cuál es la diferencia entre return y print?",     "funciones"),
    ("Mi lista da IndexError al acceder al índice",      "listas"),
    ("¿Cómo se usa if elif else en Python?",             "condicionales"),
    ("¿Qué es el caso base en recursión?",               "recursion"),
    ("¿Cómo accedo a una clave en un diccionario?",      "diccionarios"),
    ("¿Cómo se declara una variable en Python?",         "variables_y_tipos"),
    ("¿Cómo manejo excepciones con try except?",         "excepciones"),
]

ok = 0
for query, concepto in QUERIES:
    resultado = retriever.recuperar(
        query                = query,
        concepto_hint        = concepto,
        filtrar_por_concepto = True,
    )

    if resultado.fragmentos:
        frag = resultado.fragmentos[0]
        print(f"\n{VERDE}✓{RESET} [{concepto}]")
        print(f"  Query   : {query}")
        print(f"  Fuente  : {frag.capitulo} (p.{frag.pagina_aprox}) | score={frag.score}")
        print(f"  Texto   : {frag.texto[:120].strip()}...")
        ok += 1
    else:
        print(f"\n{ROJO}✗{RESET} [{concepto}] — sin fragmentos")
        print(f"  Query: {query}")

# ── Mostrar el JSON completo que recibirá la Capa 4 ──────────────────────
print(f"\n{DIM}{'─'*50}{RESET}")
print(f"{BOLD}JSON de salida hacia Capa 4 (ejemplo con ciclos):{RESET}\n")

import json
ejemplo = retriever.recuperar("¿Cómo funciona el ciclo for?", "ciclos", True)
salida = {
    "query":          ejemplo.query,
    "concepto_hint":  ejemplo.concepto_hint,
    "tiempo_ms":      ejemplo.tiempo_ms,
    "num_fragmentos": len(ejemplo.fragmentos),
    "fuentes":        ejemplo.fuentes,
    "fragmentos": [
        {
            "capitulo": f.capitulo,
            "concepto": f.concepto,
            "score":    f.score,
            "texto":    f.texto[:200] + "...",
        }
        for f in ejemplo.fragmentos
    ],
    "contexto_llm_preview": ejemplo.contexto_llm[:300] + "...",
}
print(json.dumps(salida, ensure_ascii=False, indent=2))

# ── Resumen ───────────────────────────────────────────────────────────────
print(f"\n{DIM}{'─'*50}{RESET}")
color = VERDE if ok == len(QUERIES) else ROJO
print(f"  {color}{BOLD}{ok}/{len(QUERIES)} queries con fragmentos recuperados{RESET}\n")
