"""
Tests automatizados — Capa 3 Evaluador Python
Verifica cada paso del pipeline con casos conocidos
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.evaluador import EvaluadorPython, CasoPrueba, TipoError, NivelDificultad

evaluador = EvaluadorPython(timeout_seg=3)

VERDE  = "\033[92m"
ROJO   = "\033[91m"
AMARILLO = "\033[93m"
RESET  = "\033[0m"
NEGRITA = "\033[1m"

resultados = []

def test(nombre, codigo, casos, concepto, tipo_esperado, intento=1):
    r = evaluador.evaluar(codigo, casos, concepto, intento)
    paso = r.tipo_error == tipo_esperado
    simbolo = f"{VERDE}✓{RESET}" if paso else f"{ROJO}✗{RESET}"
    resultados.append(paso)
    print(f"  {simbolo} {nombre}")
    if not paso:
        print(f"      Esperado: {tipo_esperado.value}")
        print(f"      Obtenido: {r.tipo_error.value}")
        print(f"      Mensaje:  {r.mensaje_tecnico}")
    else:
        print(f"      → {r.sugerencia_socratica}")
    return r


def seccion(titulo):
    print(f"\n{NEGRITA}{AMARILLO}{'─'*50}{RESET}")
    print(f"{NEGRITA}{titulo}{RESET}")
    print(f"{AMARILLO}{'─'*50}{RESET}")


caso_dummy = [CasoPrueba("dummy", None, "hola", "general")]
caso_numerico = [CasoPrueba("resultado", None, "10", "general")]
caso_lista = [CasoPrueba("lista", None, "[1, 2, 3]", "listas")]


seccion("PASO 2 — Validación de sintaxis")

test("Error de sintaxis: falta dos puntos en if",
     "x = 5\nif x > 3\n    print('mayor')",
     caso_dummy, "condicionales", TipoError.SINTAXIS)

test("Error de sintaxis: paréntesis no cerrado",
     "print('hola'",
     caso_dummy, "general", TipoError.SINTAXIS)

test("Error de sintaxis: indentación incorrecta",
     "def f():\nreturn 1",
     caso_dummy, "funciones", TipoError.SINTAXIS)


seccion("PASO 3 & 4 — Runtime errors")

test("NameError: variable no definida",
     "print(variable_inexistente)",
     caso_dummy, "variables", TipoError.RUNTIME)

test("IndexError: índice fuera de rango",
     "lista = [1, 2, 3]\nprint(lista[10])",
     caso_dummy, "listas", TipoError.RUNTIME)

test("ZeroDivisionError",
     "x = 10 / 0\nprint(x)",
     caso_dummy, "operaciones", TipoError.RUNTIME)

test("TypeError: suma int + str",
     "print(5 + 'texto')",
     caso_dummy, "tipos", TipoError.RUNTIME)

test("KeyError: clave inexistente en dict",
     "d = {'a': 1}\nprint(d['b'])",
     caso_dummy, "diccionarios", TipoError.RUNTIME)

test("RecursionError: recursión sin caso base",
     "def f(n):\n    return f(n-1)\nprint(f(5))",
     caso_dummy, "recursion", TipoError.RUNTIME)


seccion("PASO 4 — Timeout")

test("Ciclo infinito — debe detectar timeout",
     "while True:\n    pass",
     caso_dummy, "ciclos", TipoError.TIMEOUT)


seccion("PASO 5 & 6 — Casos de prueba y error lógico")

test("Error lógico: suma incorrecta",
     "resultado = 2 + 2\nprint(resultado)",
     [CasoPrueba("suma", None, "5", "operaciones")],
     "operaciones", TipoError.LOGICO)

test("Error lógico: lista en orden incorrecto",
     "lista = [1, 2, 3]\nprint(lista)",
     [CasoPrueba("lista invertida", None, "[3, 2, 1]", "listas")],
     "listas", TipoError.LOGICO)


seccion("PASO 7 — Código correcto")

test("Código correcto: print simple",
     "print(10)",
     [CasoPrueba("número", None, "10", "general")],
     "general", TipoError.CORRECTO)

test("Código correcto: función doble",
     "def doble(x):\n    return x * 2\nprint(doble(5))",
     [CasoPrueba("doble de 5", None, "10", "funciones")],
     "funciones", TipoError.CORRECTO)

test("Código correcto: suma de lista",
     "numeros = [1, 2, 3, 4, 5]\nprint(sum(numeros))",
     [CasoPrueba("suma lista", None, "15", "listas")],
     "listas", TipoError.CORRECTO)

test("Código correcto: invertir string",
     "s = 'Python'\nprint(s[::-1])",
     [CasoPrueba("invertir string", None, "nohtyP", "strings")],
     "strings", TipoError.CORRECTO)


seccion("Seguridad — imports prohibidos")

test("Import os bloqueado",
     "import os\nprint(os.getcwd())",
     caso_dummy, "seguridad", TipoError.SEGURIDAD)

test("Import sys bloqueado",
     "import sys\nprint(sys.version)",
     caso_dummy, "seguridad", TipoError.SEGURIDAD)

test("eval() bloqueado",
     "eval('print(1)')",
     caso_dummy, "seguridad", TipoError.SEGURIDAD)


seccion("RESUMEN")
total  = len(resultados)
pasados = sum(resultados)
pct    = round(pasados / total * 100)
color  = VERDE if pct == 100 else (AMARILLO if pct >= 80 else ROJO)
print(f"  {color}{NEGRITA}{pasados}/{total} tests pasados ({pct}%){RESET}\n")
