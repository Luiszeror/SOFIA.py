"""
CAPA 2 — Indexador de PDFs
Sistema de Tutoría Socrática UPTC

Responsabilidad:
  1. Leer los PDFs de la bibliografía (Think Python, Automate the Boring Stuff)
  2. Dividir el texto en chunks con metadatos
  3. Generar embeddings por chunk
  4. Guardar en ChromaDB (base vectorial local)

La salida de este módulo es la base de datos vectorial que el
Retriever (Capa 2b) consulta en tiempo real.
"""

import os
import re
import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Chunk:
    """Unidad mínima de texto indexado con sus metadatos."""
    chunk_id:    str        # hash único del contenido
    libro:       str        # "think_python" | "automate_boring_stuff"
    titulo_libro: str       # nombre legible del libro
    capitulo:    str        # título del capítulo detectado
    pagina_aprox: int       # página aproximada en el PDF
    concepto:    str        # concepto Python detectado automáticamente
    texto:       str        # texto del chunk
    num_tokens:  int        # estimación de tokens (chars / 4)
    posicion:    int        # índice del chunk dentro del libro


# ── Conceptos Python a detectar automáticamente en el texto ──────────────
CONCEPTOS_KEYWORDS = {
    "variables_y_tipos": [
        "variable", "integer", "float", "string", "boolean",
        "type()", "int()", "str()", "assignment", "value"
    ],
    "condicionales": [
        "if", "else", "elif", "condition", "boolean expression",
        "comparison", "True", "False", "conditional"
    ],
    "ciclos": [
        "for loop", "while loop", "iteration", "range()",
        "break", "continue", "traverse", "loop"
    ],
    "funciones": [
        "def ", "function", "return", "parameter", "argument",
        "call", "fruitful", "void function", "docstring"
    ],
    "listas": [
        "list", "append", "index", "slice", "element",
        "pop()", "sort()", "len()", "mutable"
    ],
    "strings": [
        "string", "str", "concatenat", "slice", "upper()",
        "lower()", "split()", "strip()", "format()", "f-string"
    ],
    "diccionarios": [
        "dictionary", "dict", "key", "value", "items()",
        "keys()", "values()", "get()", "hash table"
    ],
    "recursion": [
        "recursion", "recursive", "base case", "fibonacci",
        "factorial", "call stack", "infinite recursion"
    ],
    "clases": [
        "class", "object", "instance", "__init__", "method",
        "attribute", "inheritance", "self", "OOP"
    ],
    "excepciones": [
        "exception", "try", "except", "raise", "error",
        "ValueError", "TypeError", "KeyError", "traceback"
    ],
    "archivos": [
        "file", "open()", "read()", "write()", "close()",
        "with open", "path", "os.path", "directory"
    ],
}

LIBROS_CONOCIDOS = {
    "think_python":          "Think Python — Allen Downey",
    "automate_boring_stuff": "Automate the Boring Stuff — Al Sweigart",
    "python_docs":           "Documentación Python",
}


def _detectar_libro(nombre_archivo: str) -> tuple[str, str]:
    """Detecta el libro a partir del nombre del archivo PDF."""
    nombre = nombre_archivo.lower()
    if "think" in nombre or "thinkpython" in nombre:
        return "think_python", LIBROS_CONOCIDOS["think_python"]
    if "automate" in nombre or "boring" in nombre:
        return "automate_boring_stuff", LIBROS_CONOCIDOS["automate_boring_stuff"]
    # Nombre limpio como fallback
    slug = Path(nombre_archivo).stem.lower().replace(" ", "_").replace("-", "_")
    return slug, Path(nombre_archivo).stem


def _detectar_capitulo(texto: str) -> str:
    """Extrae el título del capítulo más cercano en el texto."""
    # Busca líneas que parezcan títulos de capítulo
    patrones = [
        r"^Chapter\s+\d+[:\.\s]+(.+)$",
        r"^CHAPTER\s+\d+[:\.\s]+(.+)$",
        r"^(\d+\.\s+[A-Z][^\n]{5,60})$",
        r"^([A-Z][A-Z\s]{10,50})$",    # línea toda en mayúsculas
    ]
    for linea in texto.split("\n")[:30]:
        linea = linea.strip()
        for patron in patrones:
            m = re.match(patron, linea, re.MULTILINE)
            if m:
                return m.group(1).strip()[:80]
    return "Sin título"


def _detectar_concepto(texto: str) -> str:
    """Detecta el concepto Python principal del chunk por frecuencia de keywords."""
    texto_lower = texto.lower()
    puntajes = {}
    for concepto, keywords in CONCEPTOS_KEYWORDS.items():
        puntaje = sum(texto_lower.count(kw.lower()) for kw in keywords)
        if puntaje > 0:
            puntajes[concepto] = puntaje
    if not puntajes:
        return "general"
    return max(puntajes, key=puntajes.get)


def _generar_id(texto: str, posicion: int) -> str:
    """Genera un ID único por contenido + posición."""
    contenido = f"{posicion}::{texto[:100]}"
    return hashlib.md5(contenido.encode()).hexdigest()[:12]


def _limpiar_texto(texto: str) -> str:
    """Limpia artefactos típicos de extracción PDF."""
    # Eliminar headers/footers numéricos sueltos
    texto = re.sub(r"\n\d+\n", "\n", texto)
    # Colapsar espacios múltiples
    texto = re.sub(r" {3,}", " ", texto)
    # Colapsar saltos de línea excesivos
    texto = re.sub(r"\n{4,}", "\n\n\n", texto)
    # Eliminar guiones de separación de palabras al final de línea
    texto = re.sub(r"-\n([a-z])", r"\1", texto)
    return texto.strip()


class IndexadorPDF:
    """
    Lee PDFs de la bibliografía y los convierte en chunks indexados.
    
    Flujo:
      PDF → extracción de texto → limpieza → chunking → 
      detección de metadatos → embeddings → ChromaDB
    """

    def __init__(
        self,
        directorio_pdfs: str,
        directorio_db: str,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        verbose: bool = True,
    ):
        self.directorio_pdfs = Path(directorio_pdfs)
        self.directorio_db   = Path(directorio_db)
        self.chunk_size      = chunk_size
        self.chunk_overlap   = chunk_overlap
        self.verbose         = verbose
        self.directorio_db.mkdir(parents=True, exist_ok=True)

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [RAG] {msg}")

    # ── PASO 1: Extraer texto del PDF ─────────────────────────────────────
    def extraer_texto_pdf(self, ruta_pdf: Path) -> list[tuple[int, str]]:
        """
        Extrae texto página por página.
        Retorna: lista de (numero_pagina, texto_pagina)
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("Instala pypdf: pip install pypdf")

        self._log(f"Leyendo {ruta_pdf.name}...")
        reader = PdfReader(str(ruta_pdf))
        paginas = []
        for i, pagina in enumerate(reader.pages, 1):
            texto = pagina.extract_text() or ""
            texto = _limpiar_texto(texto)
            if len(texto) > 50:   # ignorar páginas casi vacías
                paginas.append((i, texto))
        self._log(f"  → {len(paginas)} páginas con texto extraído")
        return paginas

    # ── PASO 2: Dividir en chunks ─────────────────────────────────────────
    def crear_chunks(
        self,
        paginas: list[tuple[int, str]],
        libro_id: str,
        titulo_libro: str,
    ) -> list[Chunk]:
        """
        Divide el texto en chunks de tamaño controlado con overlap.
        Cada chunk mantiene metadatos de página, capítulo y concepto.
        """
        chunks = []
        texto_completo = ""
        mapa_posicion_pagina = {}   # posicion_char → numero_pagina

        # Unir todo el texto manteniendo registro de qué página es cada parte
        for num_pag, texto_pag in paginas:
            inicio = len(texto_completo)
            texto_completo += texto_pag + "\n\n"
            for i in range(inicio, len(texto_completo)):
                mapa_posicion_pagina[i] = num_pag

        # Chunking con overlap
        inicio = 0
        posicion_chunk = 0
        while inicio < len(texto_completo):
            fin = min(inicio + self.chunk_size, len(texto_completo))

            # Extender hasta el final de la oración/párrafo si es posible
            if fin < len(texto_completo):
                for sep in ["\n\n", ". ", ".\n", "\n"]:
                    idx = texto_completo.rfind(sep, inicio, fin + 100)
                    if idx > inicio + self.chunk_size // 2:
                        fin = idx + len(sep)
                        break

            texto_chunk = texto_completo[inicio:fin].strip()
            if len(texto_chunk) < 80:
                inicio = fin - self.chunk_overlap
                continue

            pagina_aprox = mapa_posicion_pagina.get(inicio, 0)
            capitulo     = _detectar_capitulo(texto_chunk)
            concepto     = _detectar_concepto(texto_chunk)

            chunk = Chunk(
                chunk_id      = _generar_id(texto_chunk, posicion_chunk),
                libro         = libro_id,
                titulo_libro  = titulo_libro,
                capitulo      = capitulo,
                pagina_aprox  = pagina_aprox,
                concepto      = concepto,
                texto         = texto_chunk,
                num_tokens    = len(texto_chunk) // 4,
                posicion      = posicion_chunk,
            )
            chunks.append(chunk)
            posicion_chunk += 1
            inicio = fin - self.chunk_overlap

        self._log(f"  → {len(chunks)} chunks generados (size={self.chunk_size}, overlap={self.chunk_overlap})")
        return chunks

    # ── PASO 3: Guardar en ChromaDB ───────────────────────────────────────
    def indexar_en_chromadb(self, chunks: list[Chunk], coleccion_nombre: str = "corpus_python"):
        """
        Genera embeddings e indexa los chunks en ChromaDB.
        Usa sentence-transformers para los embeddings (corre local, sin API key).
        """
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "Instala: pip install chromadb sentence-transformers"
            )

        self._log("Cargando modelo de embeddings (primera vez puede tardar ~1 min)...")
        modelo = SentenceTransformer("all-MiniLM-L6-v2")

        self._log("Conectando a ChromaDB...")
        cliente = chromadb.PersistentClient(path=str(self.directorio_db))

        # Eliminar colección existente para re-indexar limpio
        try:
            cliente.delete_collection(coleccion_nombre)
        except Exception:
            pass
        coleccion = cliente.create_collection(
            name=coleccion_nombre,
            metadata={"hnsw:space": "cosine"},
        )

        # Indexar en lotes de 50
        LOTE = 50
        total = len(chunks)
        self._log(f"Indexando {total} chunks en lotes de {LOTE}...")

        for i in range(0, total, LOTE):
            lote = chunks[i : i + LOTE]
            textos    = [c.texto for c in lote]
            ids       = [c.chunk_id for c in lote]
            metadatos = [
                {
                    "libro":        c.libro,
                    "titulo_libro": c.titulo_libro,
                    "capitulo":     c.capitulo,
                    "pagina_aprox": c.pagina_aprox,
                    "concepto":     c.concepto,
                    "posicion":     c.posicion,
                    "num_tokens":   c.num_tokens,
                }
                for c in lote
            ]
            embeddings = modelo.encode(textos, show_progress_bar=False).tolist()

            coleccion.add(
                ids        = ids,
                documents  = textos,
                metadatos  = metadatos,
                embeddings = embeddings,
            )
            if self.verbose:
                pct = min(100, round((i + len(lote)) / total * 100))
                print(f"    {pct}% ({i + len(lote)}/{total} chunks)", end="\r")

        print()
        self._log(f"✓ {total} chunks indexados en ChromaDB → {self.directorio_db}")
        return coleccion

    # ── PASO 4: Guardar índice JSON de respaldo ───────────────────────────
    def guardar_indice_json(self, chunks: list[Chunk], nombre: str = "indice_rag.json"):
        """
        Guarda un índice JSON con los metadatos de todos los chunks.
        Sirve como respaldo y para debug sin necesitar ChromaDB.
        """
        ruta = self.directorio_db / nombre
        datos = {
            "total_chunks": len(chunks),
            "timestamp":    time.strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_size":   self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "libros": list({c.libro for c in chunks}),
            "conceptos": list({c.concepto for c in chunks}),
            "chunks": [
                {k: v for k, v in asdict(c).items() if k != "texto"}
                for c in chunks
            ],
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        self._log(f"✓ Índice JSON guardado → {ruta}")

    # ── Pipeline completo ─────────────────────────────────────────────────
    def indexar_directorio(self) -> dict:
        """
        Punto de entrada principal.
        Lee todos los PDFs del directorio y los indexa.
        
        Retorna un resumen del proceso.
        """
        pdfs = list(self.directorio_pdfs.glob("*.pdf"))
        if not pdfs:
            raise FileNotFoundError(
                f"No se encontraron PDFs en {self.directorio_pdfs}\n"
                f"Asegúrate de copiar los libros a esa carpeta."
            )

        self._log(f"PDFs encontrados: {[p.name for p in pdfs]}")
        todos_chunks = []

        for pdf in pdfs:
            libro_id, titulo_libro = _detectar_libro(pdf.name)
            self._log(f"\nProcesando: {titulo_libro}")

            paginas = self.extraer_texto_pdf(pdf)
            chunks  = self.crear_chunks(paginas, libro_id, titulo_libro)
            todos_chunks.extend(chunks)

        self._log(f"\nTotal: {len(todos_chunks)} chunks de {len(pdfs)} libros")

        # Guardar índice JSON (siempre, sin dependencias externas)
        self.guardar_indice_json(todos_chunks)

        # Intentar indexar en ChromaDB (requiere instalación)
        try:
            self.indexar_en_chromadb(todos_chunks)
            chromadb_ok = True
        except ImportError as e:
            self._log(f"⚠ ChromaDB no disponible ({e}). Solo se guardó el índice JSON.")
            chromadb_ok = False

        resumen = {
            "pdfs_procesados":  len(pdfs),
            "total_chunks":     len(todos_chunks),
            "chromadb_ok":      chromadb_ok,
            "directorio_db":    str(self.directorio_db),
            "libros": [
                {
                    "id":     libro_id,
                    "titulo": titulo_libro,
                    "chunks": sum(1 for c in todos_chunks if c.libro == libro_id),
                }
                for libro_id, titulo_libro in {
                    _detectar_libro(p.name) for p in pdfs
                }
            ],
        }
        return resumen
