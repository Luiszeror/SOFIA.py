"""
run_indexar.py — Ejecuta el pipeline completo de indexación
Uso: python capa2/indexador/run_indexar.py

Coloca los PDFs en:  ProyectoFinal/bibliografia/
La base vectorial se guarda en: ProyectoFinal/data/chroma_db/
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from capa2.indexador.indexador_pdf import IndexadorPDF

VERDE    = "\033[92m"
AMARILLO = "\033[93m"
ROJO     = "\033[91m"
NEGRITA  = "\033[1m"
RESET    = "\033[0m"

def main():
    # ── Rutas del proyecto ────────────────────────────────────────────────
    raiz          = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dir_pdfs      = os.path.join(raiz, "bibliografia")
    dir_db        = os.path.join(raiz, "data", "chroma_db")

    print(f"\n{NEGRITA}CAPA 2 — Indexación del corpus Python{RESET}")
    print(f"{AMARILLO}{'─' * 50}{RESET}")
    print(f"  PDFs desde : {dir_pdfs}")
    print(f"  Base de datos : {dir_db}")
    print(f"{AMARILLO}{'─' * 50}{RESET}\n")

    # ── Verificar que existen PDFs ────────────────────────────────────────
    from pathlib import Path
    pdfs = list(Path(dir_pdfs).glob("*.pdf"))
    if not pdfs:
        print(f"{ROJO}Error: No se encontraron PDFs en '{dir_pdfs}'{RESET}")
        print(f"\nAsegúrate de que la carpeta existe y contiene los libros:")
        print(f"  - think_python.pdf  (o similar)")
        print(f"  - automate_boring_stuff.pdf  (o similar)\n")
        sys.exit(1)

    print(f"PDFs encontrados ({len(pdfs)}):")
    for pdf in pdfs:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"  • {pdf.name} ({size_mb:.1f} MB)")
    print()

    # ── Ejecutar indexación ───────────────────────────────────────────────
    indexador = IndexadorPDF(
        directorio_pdfs = dir_pdfs,
        directorio_db   = dir_db,
        chunk_size      = 800,
        chunk_overlap   = 100,
        verbose         = True,
    )

    print(f"{AMARILLO}Iniciando indexación...{RESET}\n")
    resumen = indexador.indexar_directorio()

    # ── También guardar chunks con texto completo para el fallback JSON ───
    ruta_chunks_texto = Path(dir_db) / "chunks_texto.json"
    # El indexador guarda indice_rag.json sin texto; aquí guardamos CON texto
    # (esto permite el fallback sin ChromaDB)
    from capa2.indexador.indexador_pdf import _detectar_libro
    from pypdf import PdfReader
    from capa2.indexador.indexador_pdf import _limpiar_texto, _detectar_capitulo, _detectar_concepto, _generar_id

    todos_chunks_con_texto = []
    for pdf in pdfs:
        libro_id, titulo_libro = _detectar_libro(pdf.name)
        reader = PdfReader(str(pdf))
        texto_completo = ""
        for pag in reader.pages:
            texto_completo += _limpiar_texto(pag.extract_text() or "") + "\n\n"

        inicio = 0
        pos    = 0
        while inicio < len(texto_completo):
            fin = min(inicio + 800, len(texto_completo))
            for sep in ["\n\n", ". ", "\n"]:
                idx = texto_completo.rfind(sep, inicio, fin + 100)
                if idx > inicio + 400:
                    fin = idx + len(sep)
                    break
            texto = texto_completo[inicio:fin].strip()
            if len(texto) >= 80:
                todos_chunks_con_texto.append({
                    "chunk_id":     _generar_id(texto, pos),
                    "libro":        libro_id,
                    "titulo_libro": titulo_libro,
                    "capitulo":     _detectar_capitulo(texto),
                    "pagina_aprox": 0,
                    "concepto":     _detectar_concepto(texto),
                    "texto":        texto,
                    "num_tokens":   len(texto) // 4,
                    "posicion":     pos,
                })
                pos += 1
            inicio = fin - 100

    with open(ruta_chunks_texto, "w", encoding="utf-8") as f:
        json.dump(todos_chunks_con_texto, f, ensure_ascii=False)

    # ── Resumen final ─────────────────────────────────────────────────────
    print(f"\n{NEGRITA}{VERDE}✓ Indexación completada{RESET}")
    print(f"{AMARILLO}{'─' * 50}{RESET}")
    print(f"  PDFs procesados : {resumen['pdfs_procesados']}")
    print(f"  Chunks totales  : {resumen['total_chunks']}")
    print(f"  ChromaDB activo : {'Sí' if resumen['chromadb_ok'] else 'No (solo JSON)'}")
    print(f"  Guardado en     : {resumen['directorio_db']}")
    print()
    print(f"Archivos generados:")
    print(f"  • data/chroma_db/indice_rag.json    ← metadatos de todos los chunks")
    print(f"  • data/chroma_db/chunks_texto.json  ← texto completo (fallback)")
    if resumen["chromadb_ok"]:
        print(f"  • data/chroma_db/                   ← base vectorial ChromaDB")
    print(f"\nPróximo paso: python capa2/tests/test_retriever.py\n")


if __name__ == "__main__":
    main()
