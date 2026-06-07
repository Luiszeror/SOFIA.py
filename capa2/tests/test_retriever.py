"""
test_retriever.py — Verifica que el RAG recupera fragmentos relevantes
Uso: python capa2/tests/test_retriever.py

Requiere haber ejecutado run_indexar.py primero.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from capa2.retriever.retriever_rag import RetrieverRAG

VERDE    = "\033[92m"
ROJO     = "\033[91m"
AMARILLO = "\033[93m"
CYAN     = "\033[96m"
NEGRITA  = "\033[1m"
DIM      = "\033[2m"
RESET    = "\033[0m"

raiz   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
dir_db = os.path.join(raiz, "data", "chroma_db")

QUERIES_TEST = [
    {
        "query":           "¿Cómo funciona un ciclo for en Python?",
        "concepto_hint":   "ciclos",
        "descripcion":     "Pregunta básica sobre ciclos",
    },
    {
        "query":           "No entiendo por qué mi lista no se modifica dentro de la función",
        "concepto_hint":   "funciones",
        "descripcion":     "Error clásico de mutabilidad",
    },
    {
        "query":           "¿Cuál es la diferencia entre return y print?",
        "concepto_hint":   "funciones",
        "descripcion":     "Confusión frecuente en principiantes",
    },
    {
        "query":           "Mi índice da IndexError, ¿qué significa?",
        "concepto_hint":   "listas",
        "descripcion":     "Error de runtime en listas",
    },
    {
        "query":           "¿Cómo se invierte un string en Python?",
        "concepto_hint":   "strings",
        "descripcion":     "Operación básica de strings",
    },
    {
        "query":           "¿Qué es la recursión y cómo evito el stack overflow?",
        "concepto_hint":   "recursion",
        "descripcion":     "Concepto avanzado de funciones",
    },
]


def separador(titulo=""):
    ancho = 55
    if titulo:
        print(f"\n{DIM}{'─' * 3} {titulo} {'─' * (ancho - len(titulo) - 5)}{RESET}")
    else:
        print(f"{DIM}{'─' * ancho}{RESET}")


def main():
    print(f"\n{NEGRITA}CAPA 2 — Test del Retriever RAG{RESET}")
    separador()

    try:
        retriever = RetrieverRAG(
            directorio_db = dir_db,
            top_k         = 3,
            score_minimo  = 0.1,
        )
    except FileNotFoundError as e:
        print(f"\n{ROJO}Error: {e}{RESET}")
        print(f"\nEjecuta primero:")
        print(f"  python capa2/indexador/run_indexar.py\n")
        sys.exit(1)

    resultados_ok = 0

    for i, caso in enumerate(QUERIES_TEST, 1):
        separador(f"Test {i}: {caso['descripcion']}")
        print(f"  Query   : {caso['query']}")
        print(f"  Concepto: {caso['concepto_hint']}")

        resultado = retriever.recuperar(
            query          = caso["query"],
            concepto_hint  = caso["concepto_hint"],
        )

        if resultado.fragmentos:
            print(f"  {VERDE}✓ {len(resultado.fragmentos)} fragmentos recuperados ({resultado.tiempo_ms} ms){RESET}")
            for j, frag in enumerate(resultado.fragmentos, 1):
                print(f"\n    [{j}] {frag.titulo_libro}")
                print(f"        Capítulo : {frag.capitulo[:60]}")
                print(f"        Concepto : {frag.concepto} | Score: {frag.score:.3f}")
                print(f"        Texto    : {frag.texto[:120].strip()}...")
            resultados_ok += 1
        else:
            print(f"  {ROJO}✗ No se encontraron fragmentos relevantes{RESET}")

    separador("Salida JSON hacia Capa 4")
    ultimo = retriever.recuperar("¿Cómo funciona un ciclo for?", "ciclos")
    print(f"{DIM}Este es el JSON que recibe el Agente Tutor:{RESET}\n")

    salida_capa4 = {
        "query":         ultimo.query,
        "concepto_hint": ultimo.concepto_hint,
        "tiempo_ms":     ultimo.tiempo_ms,
        "top_k":         ultimo.top_k,
        "fuentes":       ultimo.fuentes,
        "num_fragmentos": len(ultimo.fragmentos),
        "fragmentos": [
            {
                "libro":        f.titulo_libro,
                "capitulo":     f.capitulo,
                "concepto":     f.concepto,
                "score":        f.score,
                "texto_preview": f.texto[:200] + "...",
            }
            for f in ultimo.fragmentos
        ],
        "contexto_llm_preview": ultimo.contexto_llm[:300] + "...",
    }
    print(json.dumps(salida_capa4, ensure_ascii=False, indent=2))

    separador("RESUMEN")
    total = len(QUERIES_TEST)
    color = VERDE if resultados_ok == total else (AMARILLO if resultados_ok > 0 else ROJO)
    print(f"  {color}{NEGRITA}{resultados_ok}/{total} queries con fragmentos recuperados{RESET}\n")


if __name__ == "__main__":
    main()
