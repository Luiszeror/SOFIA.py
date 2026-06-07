"""
CAPA 2b — Retriever RAG
Sistema de Tutoría Socrática UPTC
"""

import json
import time
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class FragmentoRecuperado:
    chunk_id:      str
    libro:         str
    titulo_libro:  str
    capitulo:      str
    pagina_aprox:  int
    concepto:      str
    texto:         str
    score:         float
    posicion:      int


@dataclass
class ResultadoRAG:
    query:          str
    concepto_hint:  str
    fragmentos:     list[FragmentoRecuperado]
    contexto_llm:   str
    fuentes:        list[str]
    tiempo_ms:      float
    top_k:          int

    def to_dict(self) -> dict:
        return asdict(self)


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
    query_lower = query.lower()
    puntajes = {}
    for concepto, keywords in CONCEPTOS_KEYWORDS.items():
        puntaje = sum(query_lower.count(kw.lower()) for kw in keywords)
        if puntaje > 0:
            puntajes[concepto] = puntaje
    return max(puntajes, key=puntajes.get) if puntajes else "general"


def _formatear_contexto(fragmentos: list[FragmentoRecuperado]) -> str:
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
    fuentes = []
    vistas = set()
    for frag in fragmentos:
        cita = f"{frag.titulo_libro}, capítulo '{frag.capitulo}' (p. {frag.pagina_aprox})"
        if cita not in vistas:
            fuentes.append(cita)
            vistas.add(cita)
    return fuentes


class RetrieverRAG:

    def __init__(
        self,
        directorio_db: str,
        top_k: int = 3,
        score_minimo: float = 0.1,
        coleccion_nombre: str = "corpus_python",
    ):
        self.directorio_db    = Path(directorio_db)
        self.top_k            = top_k
        self.score_minimo     = score_minimo
        self.coleccion_nombre = coleccion_nombre
        self._modo            = None
        self._inicializar()

    def _inicializar(self):
        """Usa el modo JSON con el corpus simplificado."""
        ruta_chunks = self.directorio_db / "chunks_texto.json"
        if ruta_chunks.exists():
            self._modo = "json"
            print(f"  [RAG] Modo: JSON ({self.directorio_db})")
            return
        raise FileNotFoundError(
            f"No se encontró chunks_texto.json en {self.directorio_db}\n"
            f"Asegúrate de tener el archivo en data/chroma_db/"
        )

    def _buscar_json(self, query: str, filtro_concepto: Optional[str] = None) -> list[FragmentoRecuperado]:
        ruta_chunks = self.directorio_db / "chunks_texto.json"
        with open(ruta_chunks, encoding="utf-8") as f:
            chunks_texto = json.load(f)

        query_tokens = set(query.lower().split())
        candidatos = []

        for chunk in chunks_texto:
            if filtro_concepto and filtro_concepto != "general":
                if chunk.get("concepto") != filtro_concepto:
                    continue
            texto_lower = chunk["texto"].lower()
            hits  = sum(1 for t in query_tokens if len(t) > 2 and t in texto_lower)
            score = hits / max(len(query_tokens), 1)
            if score >= self.score_minimo:
                candidatos.append((score, chunk))

        candidatos.sort(key=lambda x: x[0], reverse=True)

        return [
            FragmentoRecuperado(
                chunk_id     = chunk["chunk_id"],
                libro        = chunk["libro"],
                titulo_libro = chunk["titulo_libro"],
                capitulo     = chunk["capitulo"],
                pagina_aprox = chunk["pagina_aprox"],
                concepto     = chunk["concepto"],
                texto        = chunk["texto"],
                score        = round(score, 3),
                posicion     = chunk["posicion"],
            )
            for score, chunk in candidatos[: self.top_k]
        ]

    def recuperar(
        self,
        query: str,
        concepto_hint: Optional[str] = None,
        filtrar_por_concepto: bool = False,
    ) -> ResultadoRAG:
        t0 = time.perf_counter()

        concepto = concepto_hint or _detectar_concepto_query(query)
        filtro   = concepto if filtrar_por_concepto else None

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