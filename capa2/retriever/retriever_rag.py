"""
CAPA 2b — Retriever RAG
Sistema de Tutoría Socrática UPTC

Responsabilidad:
  Dado el query de un estudiante, recupera los fragmentos más
  relevantes del corpus Python y construye el contexto para el LLM.

Salida hacia Capa 4 (Agente Tutor):
  {
    "query":          str,
    "concepto_hint":  str,
    "fragmentos":     list[FragmentoRecuperado],
    "contexto_llm":   str,    ← texto listo para insertar en el prompt
    "fuentes":        list[str],
    "tiempo_ms":      float,
  }
"""

import json
import time
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class FragmentoRecuperado:
    """Un chunk recuperado con su score de relevancia."""
    chunk_id:      str
    libro:         str
    titulo_libro:  str
    capitulo:      str
    pagina_aprox:  int
    concepto:      str
    texto:         str
    score:         float       # similitud coseno (0-1, mayor = más relevante)
    posicion:      int


@dataclass
class ResultadoRAG:
    """
    Salida completa del retriever.
    Esto es lo que recibe el Agente Tutor para construir su respuesta socrática.
    """
    query:          str
    concepto_hint:  str                      # concepto detectado en el query
    fragmentos:     list[FragmentoRecuperado]
    contexto_llm:   str                      # texto formateado para el prompt
    fuentes:        list[str]                # citas legibles de las fuentes
    tiempo_ms:      float
    top_k:          int

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


CONCEPTOS_KEYWORDS = {
    "variables_y_tipos": ["variable", "tipo", "int", "str", "float", "asignar", "valor", "type"],
    "condicionales":     ["if", "else", "elif", "condición", "comparar", "booleano", "True", "False"],
    "ciclos":            ["for", "while", "ciclo", "loop", "iterar", "range", "repetir"],
    "funciones":         ["def", "función", "return", "parámetro", "argumento", "llamar"],
    "listas":            ["lista", "list", "append", "índice", "elemento", "pop", "sort"],
    "strings":           ["string", "cadena", "str", "texto", "upper", "lower", "split", "format"],
    "diccionarios":      ["dict", "diccionario", "clave", "valor", "key", "value", "items"],
    "recursion":         ["recursión", "recursiva", "base case", "fibonacci", "factorial"],
    "clases":            ["class", "clase", "objeto", "instancia", "__init__", "método", "herencia"],
    "excepciones":       ["exception", "error", "try", "except", "raise", "traceback"],
    "archivos":          ["archivo", "file", "open", "read", "write", "path"],
}


def _detectar_concepto_query(query: str) -> str:
    """Detecta el concepto Python más probable en el query del estudiante."""
    query_lower = query.lower()
    puntajes = {}
    for concepto, keywords in CONCEPTOS_KEYWORDS.items():
        puntaje = sum(query_lower.count(kw.lower()) for kw in keywords)
        if puntaje > 0:
            puntajes[concepto] = puntaje
    return max(puntajes, key=puntajes.get) if puntajes else "general"


def _formatear_contexto(fragmentos: list[FragmentoRecuperado]) -> str:
    """
    Construye el bloque de contexto que va dentro del prompt del LLM.
    El Agente Tutor inserta este bloque para anclar sus respuestas al material del curso.
    """
    if not fragmentos:
        return "No se encontraron fragmentos relevantes en el corpus."

    partes = ["=== MATERIAL DEL CURSO RELEVANTE ===\n"]
    for i, frag in enumerate(fragmentos, 1):
        partes.append(
            f"[Fuente {i}] {frag.titulo_libro} — {frag.capitulo} (p. {frag.pagina_aprox})\n"
            f"Concepto: {frag.concepto} | Relevancia: {frag.score:.2f}\n"
            f"{frag.texto}\n"
            f"{'─' * 60}\n"
        )
    partes.append("=== FIN DEL MATERIAL ===")
    return "\n".join(partes)


def _formatear_fuentes(fragmentos: list[FragmentoRecuperado]) -> list[str]:
    """Genera citas legibles para mostrar al estudiante."""
    fuentes = []
    vistas = set()
    for frag in fragmentos:
        cita = f"{frag.titulo_libro}, capítulo '{frag.capitulo}' (p. {frag.pagina_aprox})"
        if cita not in vistas:
            fuentes.append(cita)
            vistas.add(cita)
    return fuentes


class RetrieverRAG:
    """
    Consulta la base vectorial y retorna el contexto para el Agente Tutor.
    
    Soporta dos modos:
    - ChromaDB: búsqueda semántica real (modo producción)
    - JSON fallback: búsqueda por keywords (modo desarrollo sin ChromaDB)
    """

    def __init__(
        self,
        directorio_db: str,
        top_k: int = 4,
        score_minimo: float = 0.3,
        coleccion_nombre: str = "corpus_python",
    ):
        self.directorio_db      = Path(directorio_db)
        self.top_k              = top_k
        self.score_minimo       = score_minimo
        self.coleccion_nombre   = coleccion_nombre
        self._coleccion         = None
        self._modelo            = None
        self._indice_json       = None
        self._modo              = None   # "chromadb" | "json"
        self._inicializar()

    def _inicializar(self):
        """Detecta qué backend usar y lo inicializa."""
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            cliente = chromadb.PersistentClient(path=str(self.directorio_db))
            colecciones = [c.name for c in cliente.list_collections()]

            if self.coleccion_nombre in colecciones:
                self._coleccion = cliente.get_collection(self.coleccion_nombre)
                self._modelo    = SentenceTransformer("all-MiniLM-L6-v2")
                self._modo      = "chromadb"
                print(f"  [RAG] Modo: ChromaDB ({self._coleccion.count()} chunks indexados)")
                return
        except Exception:
            pass

        # Fallback: índice JSON
        ruta_json = self.directorio_db / "indice_rag.json"
        if ruta_json.exists():
            with open(ruta_json, encoding="utf-8") as f:
                self._indice_json = json.load(f)
            self._modo = "json"
            print(f"  [RAG] Modo: JSON fallback ({self._indice_json['total_chunks']} chunks)")
            return

        raise FileNotFoundError(
            "No se encontró ChromaDB ni índice JSON.\n"
            "Ejecuta primero: python capa2/indexador/run_indexar.py"
        )

    # ── Búsqueda semántica con ChromaDB ──────────────────────────────────
    def _buscar_chromadb(self, query: str, filtro_concepto: Optional[str] = None) -> list[FragmentoRecuperado]:
        embedding_query = self._modelo.encode([query]).tolist()

        where = {"concepto": filtro_concepto} if filtro_concepto and filtro_concepto != "general" else None

        kwargs = {
            "query_embeddings": embedding_query,
            "n_results":        self.top_k,
            "include":          ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        resultados = self._coleccion.query(**kwargs)

        fragmentos = []
        for i, (doc, meta, dist) in enumerate(zip(
            resultados["documents"][0],
            resultados["metadatas"][0],
            resultados["distances"][0],
        )):
            score = 1 - dist   # distancia coseno → similitud
            if score < self.score_minimo:
                continue
            fragmentos.append(FragmentoRecuperado(
                chunk_id     = resultados["ids"][0][i],
                libro        = meta.get("libro", ""),
                titulo_libro = meta.get("titulo_libro", ""),
                capitulo     = meta.get("capitulo", ""),
                pagina_aprox = meta.get("pagina_aprox", 0),
                concepto     = meta.get("concepto", "general"),
                texto        = doc,
                score        = round(score, 3),
                posicion     = meta.get("posicion", i),
            ))
        return fragmentos

    # ── Búsqueda por keywords en JSON (fallback) ──────────────────────────
    def _buscar_json(self, query: str, filtro_concepto: Optional[str] = None) -> list[FragmentoRecuperado]:
        """
        Búsqueda simple por frecuencia de términos.
        Menos precisa que embeddings pero funciona sin dependencias externas.
        """
        query_tokens = set(query.lower().split())
        candidatos   = []

        # Necesitamos el texto completo — buscamos en el archivo de chunks completo
        ruta_chunks = self.directorio_db / "chunks_texto.json"
        if not ruta_chunks.exists():
            return []

        with open(ruta_chunks, encoding="utf-8") as f:
            chunks_texto = json.load(f)

        for chunk in chunks_texto:
            if filtro_concepto and filtro_concepto != "general":
                if chunk.get("concepto") != filtro_concepto:
                    continue
            texto_lower = chunk["texto"].lower()
            # Score: fracción de tokens del query presentes en el chunk
            hits  = sum(1 for t in query_tokens if t in texto_lower)
            score = hits / max(len(query_tokens), 1)
            if score >= 0.1:
                candidatos.append((score, chunk))

        candidatos.sort(key=lambda x: x[0], reverse=True)

        fragmentos = []
        for score, chunk in candidatos[: self.top_k]:
            fragmentos.append(FragmentoRecuperado(
                chunk_id     = chunk["chunk_id"],
                libro        = chunk["libro"],
                titulo_libro = chunk["titulo_libro"],
                capitulo     = chunk["capitulo"],
                pagina_aprox = chunk["pagina_aprox"],
                concepto     = chunk["concepto"],
                texto        = chunk["texto"],
                score        = round(score, 3),
                posicion     = chunk["posicion"],
            ))
        return fragmentos

    # ── Método principal ──────────────────────────────────────────────────
    def recuperar(
        self,
        query: str,
        concepto_hint: Optional[str] = None,
        filtrar_por_concepto: bool = False,
    ) -> ResultadoRAG:
        """
        Punto de entrada principal del retriever.
        
        Args:
            query:               Pregunta o código del estudiante
            concepto_hint:       Concepto ya detectado por la Capa 3 (opcional)
            filtrar_por_concepto: Si True, solo busca chunks de ese concepto
        
        Returns:
            ResultadoRAG con fragmentos + contexto listo para el Agente Tutor
        """
        t0 = time.perf_counter()

        concepto = concepto_hint or _detectar_concepto_query(query)
        filtro   = concepto if filtrar_por_concepto else None

        if self._modo == "chromadb":
            fragmentos = self._buscar_chromadb(query, filtro)
            # Si no hay resultados con filtro, buscar sin filtro
            if not fragmentos and filtro:
                fragmentos = self._buscar_chromadb(query, None)
        else:
            fragmentos = self._buscar_json(query, filtro)
            if not fragmentos and filtro:
                fragmentos = self._buscar_json(query, None)

        tiempo_ms = round((time.perf_counter() - t0) * 1000, 2)

        return ResultadoRAG(
            query         = query,
            concepto_hint = concepto,
            fragmentos    = fragmentos,
            contexto_llm  = _formatear_contexto(fragmentos),
            fuentes       = _formatear_fuentes(fragmentos),
            tiempo_ms     = tiempo_ms,
            top_k         = self.top_k,
        )
