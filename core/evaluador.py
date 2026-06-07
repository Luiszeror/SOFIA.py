"""
CAPA 3 — Evaluador de Código Python
Sistema de Tutoría Socrática UPTC

Pipeline:
  1. Recibir código
  2. Validar sintaxis (ast)
  3. Ejecutar en sandbox
  4. Detectar runtime errors
  5. Ejecutar casos de prueba
  6. Clasificar errores
  7. Retornar JSON estructurado
"""

import ast
import sys
import io
import time
import signal
import threading
import traceback
import textwrap
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

# Windows no tiene SIGALRM — usamos threading.Timer como alternativa
_WINDOWS = sys.platform == "win32"


class TipoError(str, Enum):
    SINTAXIS    = "error_sintaxis"
    RUNTIME     = "error_runtime"
    LOGICO      = "error_logico"
    TIMEOUT     = "error_timeout"
    SEGURIDAD   = "error_seguridad"
    CORRECTO    = "correcto"


class NivelDificultad(str, Enum):
    BASICO      = "basico"
    INTERMEDIO  = "intermedio"
    AVANZADO    = "avanzado"


@dataclass
class CasoPrueba:
    descripcion: str
    entrada: Optional[str]       
    salida_esperada: str
    concepto: str
    dificultad: NivelDificultad = NivelDificultad.BASICO


@dataclass
class ResultadoCaso:
    descripcion: str
    salida_esperada: str
    salida_obtenida: str
    paso: bool
    tiempo_ms: float


@dataclass
class ResultadoEvaluacion:
    tipo_error: TipoError
    concepto: str
    mensaje_tecnico: str
    linea_error: Optional[int]
    casos_ejecutados: int
    casos_pasados: int
    resultados_casos: list[ResultadoCaso]
    tiempo_total_ms: float
    intento_numero: int
    sugerencia_socratica: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tipo_error"] = self.tipo_error.value
        return d


NODOS_PROHIBIDOS = {
    "Import", "ImportFrom",
}

NOMBRES_PROHIBIDOS = {
    "__import__", "exec", "eval", "compile",
    "open", "input", "__builtins__",
    "os", "sys", "subprocess", "socket",
    "shutil", "pathlib",
}


class AnalizadorSeguridad(ast.NodeVisitor):
    """Recorre el AST buscando patrones peligrosos."""

    def __init__(self):
        self.violaciones: list[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            self.violaciones.append(
                f"Importación no permitida: '{alias.name}' (línea {node.lineno})"
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.violaciones.append(
            f"Importación no permitida: 'from {node.module} import ...' (línea {node.lineno})"
        )
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in NOMBRES_PROHIBIDOS:
                self.violaciones.append(
                    f"Función no permitida: '{node.func.id}' (línea {node.lineno})"
                )
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            if node.value.id in NOMBRES_PROHIBIDOS:
                self.violaciones.append(
                    f"Acceso no permitido: '{node.value.id}.{node.attr}'"
                )
        self.generic_visit(node)


class SandboxPython:
    """
    Entorno de ejecución controlado.
    Restringe builtins, captura stdout/stderr, limita tiempo.
    """

    BUILTINS_PERMITIDOS = {
        "print", "range", "len", "int", "float", "str", "bool",
        "list", "dict", "tuple", "set", "type", "isinstance",
        "enumerate", "zip", "map", "filter", "sorted", "reversed",
        "min", "max", "sum", "abs", "round", "divmod", "pow",
        "True", "False", "None", "repr", "format",
        "any", "all", "chr", "ord", "hex", "bin", "oct",
        "hasattr", "getattr", "setattr", "callable",
        "StopIteration", "ValueError", "TypeError", "IndexError",
        "KeyError", "AttributeError", "ZeroDivisionError",
        "Exception", "RuntimeError", "OverflowError",
        "NotImplementedError", "AssertionError",
    }

    def __init__(self, timeout_seg: int = 5):
        self.timeout_seg = timeout_seg

    def ejecutar(self, codigo: str, entrada_stdin: Optional[str] = None) -> dict:
        """
        Ejecuta el código en el sandbox — compatible con Windows y Linux/Mac.
        Usa threading.Timer para el timeout (funciona en todos los SO).
        Retorna: {stdout, stderr, excepcion, tipo_excepcion, linea_error, tiempo_ms}
        """
        import builtins as _builtins_mod

        builtins_restringidos = {
            name: getattr(_builtins_mod, name)
            for name in self.BUILTINS_PERMITIDOS
            if hasattr(_builtins_mod, name)
        }

        stdout_capturado = io.StringIO()
        stderr_capturado = io.StringIO()
        namespace         = {"__builtins__": builtins_restringidos}
        resultado         = {}   # se llena desde el hilo worker

        def worker():
            """Ejecuta el código en un hilo separado con stdout/stderr capturados."""
            stdin_original = sys.stdin
            old_stdout     = sys.stdout
            old_stderr     = sys.stderr
            try:
                if entrada_stdin:
                    sys.stdin = io.StringIO(entrada_stdin)
                sys.stdout = stdout_capturado
                sys.stderr = stderr_capturado
                exec(codigo, namespace)  # noqa: S102
                resultado["excepcion"]      = None
                resultado["tipo_excepcion"] = None
                resultado["linea_error"]    = None

            except SyntaxError as e:
                resultado["excepcion"]      = str(e)
                resultado["tipo_excepcion"] = "SyntaxError"
                resultado["linea_error"]    = e.lineno

            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                resultado["excepcion"]      = f"{type(e).__name__}: {e}"
                resultado["tipo_excepcion"] = type(e).__name__
                resultado["linea_error"]    = tb[-1].lineno if tb else None

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin  = stdin_original

        t_inicio = time.perf_counter()

        hilo = threading.Thread(target=worker, daemon=True)
        hilo.start()
        hilo.join(timeout=self.timeout_seg)

        t_fin      = time.perf_counter()
        tiempo_ms  = round((t_fin - t_inicio) * 1000, 2)

        # Si el hilo sigue vivo, hubo timeout
        if hilo.is_alive():
            return {
                "stdout":         "",
                "stderr":         "",
                "excepcion":      f"El código tardó más de {self.timeout_seg} segundos.",
                "tipo_excepcion": "TimeoutError",
                "linea_error":    None,
                "tiempo_ms":      tiempo_ms,
            }

        return {
            "stdout":         stdout_capturado.getvalue().strip(),
            "stderr":         stderr_capturado.getvalue().strip(),
            "excepcion":      resultado.get("excepcion"),
            "tipo_excepcion": resultado.get("tipo_excepcion"),
            "linea_error":    resultado.get("linea_error"),
            "tiempo_ms":      tiempo_ms,
        }


SUGERENCIAS_SOCRATICAS = {
    TipoError.SINTAXIS: [
        "¿Qué espera Python encontrar al final de esa línea?",
        "¿Todos tus bloques de código tienen los dos puntos (:) necesarios?",
        "¿La indentación de ese bloque es consistente con el resto?",
    ],
    TipoError.RUNTIME: {
        "IndexError":        "¿Cuál es el índice del último elemento de esa lista?",
        "TypeError":         "¿De qué tipo son los valores que estás combinando?",
        "ZeroDivisionError": "¿Qué pasa cuando el denominador es cero?",
        "NameError":         "¿En qué punto de tu código defines esa variable?",
        "KeyError":          "¿Cómo podrías verificar si una clave existe antes de usarla?",
        "AttributeError":    "¿Ese tipo de dato tiene ese método o atributo?",
        "RecursionError":    "¿Cuál es el caso base de tu recursión?",
        "default":           "¿Qué estaba pasando en el programa justo antes del error?",
    },
    TipoError.LOGICO: [
        "¿El resultado que obtuviste tiene sentido para ese caso de prueba?",
        "¿Qué valor debería tener la variable principal al final de la ejecución?",
        "¿Tu algoritmo maneja correctamente los casos límite (lista vacía, cero, negativo)?",
    ],
    TipoError.TIMEOUT: [
        "¿Tu ciclo tiene una condición de parada que siempre se cumple?",
        "¿La variable de control del ciclo cambia en cada iteración?",
    ],
    TipoError.SEGURIDAD: [
        "En este entorno trabajamos sin importaciones externas. ¿Puedes resolver esto solo con las funciones básicas de Python?",
    ],
    TipoError.CORRECTO: [
        "¡Correcto! ¿Podrías explicar con tus palabras por qué funciona tu solución?",
        "¡Bien hecho! ¿Qué pasaría si el input fuera una lista vacía?",
        "¡Excelente! ¿Hay alguna forma de hacer esto en menos líneas?",
    ],
}


def _get_sugerencia(tipo: TipoError, tipo_exc: Optional[str] = None) -> str:
    import random
    pool = SUGERENCIAS_SOCRATICAS[tipo]
    if isinstance(pool, dict):
        return pool.get(tipo_exc or "default", pool["default"])
    return random.choice(pool)


class EvaluadorPython:
    """
    Clase principal de la Capa 3.
    Orquesta todo el pipeline de evaluación.
    """

    def __init__(self, timeout_seg: int = 5):
        self.sandbox = SandboxPython(timeout_seg)

    def evaluar(
        self,
        codigo: str,
        casos_de_prueba: list[CasoPrueba],
        concepto: str = "general",
        intento_numero: int = 1,
    ) -> ResultadoEvaluacion:

        t_total_inicio = time.perf_counter()
        codigo = textwrap.dedent(codigo).strip()

        # ── PASO 1: Validación de seguridad ──────────────────────────────
        try:
            arbol = ast.parse(codigo)
        except SyntaxError as e:
            return self._resultado_sintaxis(e, concepto, intento_numero,
                                            time.perf_counter() - t_total_inicio)

        analizador = AnalizadorSeguridad()
        analizador.visit(arbol)
        if analizador.violaciones:
            return ResultadoEvaluacion(
                tipo_error        = TipoError.SEGURIDAD,
                concepto          = concepto,
                mensaje_tecnico   = " | ".join(analizador.violaciones),
                linea_error       = None,
                casos_ejecutados  = 0,
                casos_pasados     = 0,
                resultados_casos  = [],
                tiempo_total_ms   = round((time.perf_counter() - t_total_inicio) * 1000, 2),
                intento_numero    = intento_numero,
                sugerencia_socratica = _get_sugerencia(TipoError.SEGURIDAD),
            )

        # ── PASO 2: Validación de sintaxis (AST) ─────────────────────────
        try:
            compile(codigo, "<codigo_estudiante>", "exec")
        except SyntaxError as e:
            return self._resultado_sintaxis(e, concepto, intento_numero,
                                            time.perf_counter() - t_total_inicio)

        # ── PASO 3 & 4: Ejecución base — detectar runtime errors ─────────
        resultado_base = self.sandbox.ejecutar(codigo)

        if resultado_base["tipo_excepcion"] == "TimeoutError":
            return ResultadoEvaluacion(
                tipo_error        = TipoError.TIMEOUT,
                concepto          = concepto,
                mensaje_tecnico   = resultado_base["excepcion"],
                linea_error       = None,
                casos_ejecutados  = 0,
                casos_pasados     = 0,
                resultados_casos  = [],
                tiempo_total_ms   = round((time.perf_counter() - t_total_inicio) * 1000, 2),
                intento_numero    = intento_numero,
                sugerencia_socratica = _get_sugerencia(TipoError.TIMEOUT),
            )

        if resultado_base["excepcion"] and "SyntaxError" in (resultado_base["tipo_excepcion"] or ""):
            return self._resultado_sintaxis_str(
                resultado_base, concepto, intento_numero,
                time.perf_counter() - t_total_inicio
            )

        # ── PASO 5: Ejecutar casos de prueba ─────────────────────────────
        resultados_casos: list[ResultadoCaso] = []
        hay_runtime_error = False
        tipo_runtime = None
        linea_runtime = None
        msg_runtime = None

        for caso in casos_de_prueba:
            res = self.sandbox.ejecutar(codigo, caso.entrada)

            if res["excepcion"] and "Timeout" not in (res["tipo_excepcion"] or ""):
                hay_runtime_error = True
                tipo_runtime  = res["tipo_excepcion"]
                linea_runtime = res["linea_error"]
                msg_runtime   = res["excepcion"]
                resultados_casos.append(ResultadoCaso(
                    descripcion      = caso.descripcion,
                    salida_esperada  = caso.salida_esperada,
                    salida_obtenida  = f"ERROR: {res['excepcion']}",
                    paso             = False,
                    tiempo_ms        = res["tiempo_ms"],
                ))
                continue

            salida_limpia   = res["stdout"].strip()
            esperada_limpia = caso.salida_esperada.strip()
            paso = salida_limpia == esperada_limpia

            resultados_casos.append(ResultadoCaso(
                descripcion     = caso.descripcion,
                salida_esperada = caso.salida_esperada,
                salida_obtenida = res["stdout"],
                paso            = paso,
                tiempo_ms       = res["tiempo_ms"],
            ))

        # ── PASO 6: Clasificar el error global ───────────────────────────
        casos_pasados = sum(1 for r in resultados_casos if r.paso)

        if hay_runtime_error:
            tipo_final = TipoError.RUNTIME
            sugerencia = _get_sugerencia(TipoError.RUNTIME, tipo_runtime)
            msg_final  = msg_runtime or "Error en tiempo de ejecución"
            linea_f    = linea_runtime
        elif casos_pasados == len(casos_de_prueba):
            tipo_final = TipoError.CORRECTO
            sugerencia = _get_sugerencia(TipoError.CORRECTO)
            msg_final  = "Todos los casos de prueba pasaron correctamente."
            linea_f    = None
        else:
            tipo_final = TipoError.LOGICO
            sugerencia = _get_sugerencia(TipoError.LOGICO)
            msg_final  = (
                f"{casos_pasados}/{len(casos_de_prueba)} casos correctos. "
                "El código corre pero produce resultados incorrectos."
            )
            linea_f = None

        tiempo_total_ms = round((time.perf_counter() - t_total_inicio) * 1000, 2)

        # ── PASO 7: Retornar JSON estructurado ────────────────────────────
        return ResultadoEvaluacion(
            tipo_error           = tipo_final,
            concepto             = concepto,
            mensaje_tecnico      = msg_final,
            linea_error          = linea_f,
            casos_ejecutados     = len(casos_de_prueba),
            casos_pasados        = casos_pasados,
            resultados_casos     = resultados_casos,
            tiempo_total_ms      = tiempo_total_ms,
            intento_numero       = intento_numero,
            sugerencia_socratica = sugerencia,
            metadata             = {
                "longitud_codigo_chars": len(codigo),
                "num_nodos_ast": sum(1 for _ in ast.walk(arbol)),
            },
        )

    def _resultado_sintaxis(self, e: SyntaxError, concepto, intento, t) -> ResultadoEvaluacion:
        return ResultadoEvaluacion(
            tipo_error           = TipoError.SINTAXIS,
            concepto             = concepto,
            mensaje_tecnico      = f"SyntaxError: {e.msg} (línea {e.lineno})",
            linea_error          = e.lineno,
            casos_ejecutados     = 0,
            casos_pasados        = 0,
            resultados_casos     = [],
            tiempo_total_ms      = round(t * 1000, 2),
            intento_numero       = intento,
            sugerencia_socratica = _get_sugerencia(TipoError.SINTAXIS),
        )

    def _resultado_sintaxis_str(self, res, concepto, intento, t) -> ResultadoEvaluacion:
        return ResultadoEvaluacion(
            tipo_error           = TipoError.SINTAXIS,
            concepto             = concepto,
            mensaje_tecnico      = res["excepcion"],
            linea_error          = res["linea_error"],
            casos_ejecutados     = 0,
            casos_pasados        = 0,
            resultados_casos     = [],
            tiempo_total_ms      = round(t * 1000, 2),
            intento_numero       = intento,
            sugerencia_socratica = _get_sugerencia(TipoError.SINTAXIS),
        )
