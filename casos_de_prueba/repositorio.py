"""
Repositorio de casos de prueba para conceptos de Python
Organizados siguiendo la estructura de Think Python y Automate the Boring Stuff
"""

from core.evaluador import CasoPrueba, NivelDificultad

CASOS_POR_CONCEPTO: dict[str, list[CasoPrueba]] = {

    "variables_y_tipos": [
        CasoPrueba(
            descripcion     = "Asignar e imprimir un entero",
            entrada         = None,
            salida_esperada = "42",
            concepto        = "variables_y_tipos",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Operación aritmética básica",
            entrada         = None,
            salida_esperada = "15",
            concepto        = "variables_y_tipos",
            dificultad      = NivelDificultad.BASICO,
        ),
    ],

    "condicionales": [
        CasoPrueba(
            descripcion     = "Número positivo",
            entrada         = None,
            salida_esperada = "positivo",
            concepto        = "condicionales",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Número negativo",
            entrada         = None,
            salida_esperada = "negativo",
            concepto        = "condicionales",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Cero",
            entrada         = None,
            salida_esperada = "cero",
            concepto        = "condicionales",
            dificultad      = NivelDificultad.BASICO,
        ),
    ],

    "ciclos": [
        CasoPrueba(
            descripcion     = "Imprimir números del 1 al 5",
            entrada         = None,
            salida_esperada = "1\n2\n3\n4\n5",
            concepto        = "ciclos",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Suma acumulada del 1 al 10",
            entrada         = None,
            salida_esperada = "55",
            concepto        = "ciclos",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Tabla del 3",
            entrada         = None,
            salida_esperada = "3\n6\n9\n12\n15\n18\n21\n24\n27\n30",
            concepto        = "ciclos",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
    ],

    "funciones": [
        CasoPrueba(
            descripcion     = "Función que retorna el doble",
            entrada         = None,
            salida_esperada = "10",
            concepto        = "funciones",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Función factorial de 5",
            entrada         = None,
            salida_esperada = "120",
            concepto        = "funciones",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
        CasoPrueba(
            descripcion     = "Función que verifica si es par",
            entrada         = None,
            salida_esperada = "True\nFalse",
            concepto        = "funciones",
            dificultad      = NivelDificultad.BASICO,
        ),
    ],

    "listas": [
        CasoPrueba(
            descripcion     = "Suma de todos los elementos",
            entrada         = None,
            salida_esperada = "15",
            concepto        = "listas",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Invertir una lista",
            entrada         = None,
            salida_esperada = "[5, 4, 3, 2, 1]",
            concepto        = "listas",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
        CasoPrueba(
            descripcion     = "Filtrar solo los pares",
            entrada         = None,
            salida_esperada = "[2, 4, 6]",
            concepto        = "listas",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
    ],

    "diccionarios": [
        CasoPrueba(
            descripcion     = "Acceder a un valor por clave",
            entrada         = None,
            salida_esperada = "Python",
            concepto        = "diccionarios",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Contar frecuencia de caracteres",
            entrada         = None,
            salida_esperada = "{'h': 1, 'o': 1, 'l': 2, 'a': 1}",
            concepto        = "diccionarios",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
    ],

    "recursion": [
        CasoPrueba(
            descripcion     = "Fibonacci de 6",
            entrada         = None,
            salida_esperada = "8",
            concepto        = "recursion",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
        CasoPrueba(
            descripcion     = "Suma recursiva del 1 al n",
            entrada         = None,
            salida_esperada = "10",
            concepto        = "recursion",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
    ],

    "strings": [
        CasoPrueba(
            descripcion     = "Invertir un string",
            entrada         = None,
            salida_esperada = "nohtyP",
            concepto        = "strings",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Contar vocales",
            entrada         = None,
            salida_esperada = "3",
            concepto        = "strings",
            dificultad      = NivelDificultad.BASICO,
        ),
        CasoPrueba(
            descripcion     = "Verificar palíndromo",
            entrada         = None,
            salida_esperada = "True\nFalse",
            concepto        = "strings",
            dificultad      = NivelDificultad.INTERMEDIO,
        ),
    ],
}


def obtener_casos(concepto: str) -> list[CasoPrueba]:
    """Retorna los casos de prueba para un concepto dado."""
    return CASOS_POR_CONCEPTO.get(concepto, [])


def listar_conceptos() -> list[str]:
    """Lista todos los conceptos disponibles."""
    return list(CASOS_POR_CONCEPTO.keys())
