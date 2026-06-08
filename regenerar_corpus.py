"""
regenerar_corpus.py
Regenera chunks_texto.json e indice_rag.json desde los PDFs de bibliografia/
Ejecutar: python regenerar_corpus.py
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypdf import PdfReader

VERDE  = "\033[92m"; AMARILLO = "\033[93m"; NEGRITA = "\033[1m"; RESET = "\033[0m"

MAPA_CAPITULOS = {
    # Palabras clave → (concepto, capitulo)
    "variable": ("variables_y_tipos", "Cap 1: Variables y Tipos"),
    "int(":     ("variables_y_tipos", "Cap 1: Variables y Tipos"),
    "str(":     ("variables_y_tipos", "Cap 1: Variables y Tipos"),
    "if ":      ("condicionales",     "Cap 2: Condicionales"),
    "elif":     ("condicionales",     "Cap 2: Condicionales"),
    "for ":     ("ciclos",            "Cap 3: Ciclos"),
    "while ":   ("ciclos",            "Cap 3: Ciclos"),
    "range(":   ("ciclos",            "Cap 3: Ciclos"),
    "def ":     ("funciones",         "Cap 4: Funciones"),
    "return":   ("funciones",         "Cap 4: Funciones"),
    "list":     ("listas",            "Cap 5: Listas"),
    "append":   ("listas",            "Cap 5: Listas"),
    "string":   ("strings",           "Cap 6: Strings"),
    "upper()":  ("strings",           "Cap 6: Strings"),
    "split()":  ("strings",           "Cap 6: Strings"),
    "dict":     ("diccionarios",      "Cap 7: Diccionarios"),
    "clave":    ("diccionarios",      "Cap 7: Diccionarios"),
    "recursion":("recursion",         "Cap 8: Recursión"),
    "factorial":("recursion",         "Cap 8: Recursión"),
    "fibonacci":("recursion",         "Cap 8: Recursión"),
    "class ":   ("clases",            "Cap 9: Clases"),
    "__init__": ("clases",            "Cap 9: Clases"),
    "except":   ("excepciones",       "Cap 10: Excepciones"),
    "try:":     ("excepciones",       "Cap 10: Excepciones"),
}

def detectar_concepto_capitulo(texto):
    texto_lower = texto.lower()
    puntajes = {}
    for kw, (concepto, cap) in MAPA_CAPITULOS.items():
        if kw.lower() in texto_lower:
            puntajes[concepto] = puntajes.get(concepto, 0) + 1
    if not puntajes:
        return "general", "General"
    concepto = max(puntajes, key=puntajes.get)
    cap = next(c for k, (co, c) in MAPA_CAPITULOS.items() if co == concepto)
    return concepto, cap

def procesar_pdf(ruta_pdf):
    reader   = PdfReader(str(ruta_pdf))
    nombre   = os.path.basename(ruta_pdf)
    libro_id = "corpus_python_v2" if "v2" in nombre else "corpus_python"
    titulo   = "Fundamentos de Python v2 — SOFIA" if "v2" in nombre else "Fundamentos de Python — SOFIA"

    chunks = []
    pos    = 0
    for num_pag, pagina in enumerate(reader.pages, 1):
        texto = (pagina.extract_text() or "").strip()
        if len(texto) < 50:
            continue
        concepto, capitulo = detectar_concepto_capitulo(texto)
        cid = hashlib.md5(f"{pos}:{texto[:60]}".encode()).hexdigest()[:8]
        chunks.append({
            "chunk_id":     cid,
            "libro":        libro_id,
            "titulo_libro": titulo,
            "capitulo":     capitulo,
            "pagina_aprox": num_pag,
            "concepto":     concepto,
            "texto":        texto,
            "num_tokens":   len(texto) // 4,
            "posicion":     pos,
        })
        pos += 1
    return chunks

def main():
    raiz      = os.path.dirname(os.path.abspath(__file__))
    dir_biblio = os.path.join(raiz, "bibliografia")
    dir_db     = os.path.join(raiz, "data", "chroma_db")
    os.makedirs(dir_db, exist_ok=True)

    pdfs = [f for f in os.listdir(dir_biblio) if f.endswith(".pdf")]
    if not pdfs:
        print(f"\033[91mNo se encontraron PDFs en {dir_biblio}\033[0m")
        return

    print(f"\n{NEGRITA}Regenerando corpus RAG{RESET}")
    print(f"{AMARILLO}PDFs encontrados: {pdfs}{RESET}\n")

    todos_chunks = []
    for pdf in pdfs:
        ruta = os.path.join(dir_biblio, pdf)
        print(f"  Procesando {pdf}...")
        chunks = procesar_pdf(ruta)
        todos_chunks.extend(chunks)
        print(f"  → {len(chunks)} chunks extraídos")

    # Guardar chunks_texto.json
    ruta_chunks = os.path.join(dir_db, "chunks_texto.json")
    with open(ruta_chunks, "w", encoding="utf-8") as f:
        json.dump(todos_chunks, f, ensure_ascii=False, indent=2)

    # Guardar indice_rag.json (sin texto)
    indice = {
        "total_chunks": len(todos_chunks),
        "libros":    list({c["libro"] for c in todos_chunks}),
        "conceptos": list({c["concepto"] for c in todos_chunks}),
        "chunks":    [{k:v for k,v in c.items() if k != "texto"} for c in todos_chunks],
    }
    ruta_indice = os.path.join(dir_db, "indice_rag.json")
    with open(ruta_indice, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    print(f"\n{VERDE}{NEGRITA}✓ Corpus regenerado{RESET}")
    print(f"  Total chunks : {len(todos_chunks)}")
    print(f"  Guardado en  : {dir_db}\n")

if __name__ == "__main__":
    main()
