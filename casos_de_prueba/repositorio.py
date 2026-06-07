"""
Repositorio de casos de prueba — UN solo caso por ejercicio
para que el estudiante pueda resolver uno a la vez.
"""

from core.evaluador import CasoPrueba, NivelDificultad

EJERCICIOS = {
    "ciclos": [
        {
            "nombre":      "Imprimir del 1 al 5",
            "descripcion": "Usa un ciclo for con range() para imprimir los números del 1 al 5, uno por línea.",
            "casos": [CasoPrueba("imprime 1 al 5", None, "1\n2\n3\n4\n5", "ciclos", NivelDificultad.BASICO)],
            "codigo_correcto": "for i in range(1, 6):\n    print(i)",
        },
        {
            "nombre":      "Suma del 1 al 10",
            "descripcion": "Usa un ciclo para calcular la suma de los números del 1 al 10 e imprime el resultado.",
            "casos": [CasoPrueba("suma 1 al 10", None, "55", "ciclos", NivelDificultad.BASICO)],
            "codigo_correcto": "total = 0\nfor i in range(1, 11):\n    total += i\nprint(total)",
        },
        {
            "nombre":      "Tabla del 3",
            "descripcion": "Imprime los primeros 10 múltiplos del 3 (del 3 al 30), uno por línea.",
            "casos": [CasoPrueba("tabla del 3", None, "3\n6\n9\n12\n15\n18\n21\n24\n27\n30", "ciclos", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "for i in range(1, 11):\n    print(3 * i)",
        },
    ],
    "funciones": [
        {
            "nombre":      "Función doble",
            "descripcion": "Escribe una función llamada doble(x) que retorne el doble de x. Llámala con doble(5) e imprime el resultado.",
            "casos": [CasoPrueba("doble de 5", None, "10", "funciones", NivelDificultad.BASICO)],
            "codigo_correcto": "def doble(x):\n    return x * 2\nprint(doble(5))",
        },
        {
            "nombre":      "Factorial",
            "descripcion": "Escribe una función factorial(n) que calcule el factorial de n. Imprime factorial(5).",
            "casos": [CasoPrueba("factorial de 5", None, "120", "funciones", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)\nprint(factorial(5))",
        },
        {
            "nombre":      "¿Es par?",
            "descripcion": "Escribe una función es_par(n) que retorne True si n es par y False si no. Imprime es_par(4) y es_par(3).",
            "casos": [CasoPrueba("es par", None, "True\nFalse", "funciones", NivelDificultad.BASICO)],
            "codigo_correcto": "def es_par(n):\n    return n % 2 == 0\nprint(es_par(4))\nprint(es_par(3))",
        },
    ],
    "listas": [
        {
            "nombre":      "Suma de lista",
            "descripcion": "Dada la lista [1, 2, 3, 4, 5], calcula e imprime la suma de todos sus elementos sin usar sum().",
            "casos": [CasoPrueba("suma lista", None, "15", "listas", NivelDificultad.BASICO)],
            "codigo_correcto": "numeros = [1, 2, 3, 4, 5]\ntotal = 0\nfor n in numeros:\n    total += n\nprint(total)",
        },
        {
            "nombre":      "Invertir lista",
            "descripcion": "Dada la lista [1, 2, 3, 4, 5], imprímela invertida: [5, 4, 3, 2, 1].",
            "casos": [CasoPrueba("lista invertida", None, "[5, 4, 3, 2, 1]", "listas", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "numeros = [1, 2, 3, 4, 5]\nprint(numeros[::-1])",
        },
        {
            "nombre":      "Filtrar pares",
            "descripcion": "Dada la lista [1, 2, 3, 4, 5, 6], imprime solo los números pares: [2, 4, 6].",
            "casos": [CasoPrueba("pares", None, "[2, 4, 6]", "listas", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "numeros = [1, 2, 3, 4, 5, 6]\nprint([x for x in numeros if x % 2 == 0])",
        },
    ],
    "strings": [
        {
            "nombre":      "Invertir string",
            "descripcion": "Invierte el string 'Python' e imprímelo. Resultado esperado: nohtyP",
            "casos": [CasoPrueba("invertir string", None, "nohtyP", "strings", NivelDificultad.BASICO)],
            "codigo_correcto": "s = 'Python'\nprint(s[::-1])",
        },
        {
            "nombre":      "Contar vocales",
            "descripcion": "Cuenta e imprime cuántas vocales tiene la palabra 'murciélago'. Resultado: 5",
            "casos": [CasoPrueba("contar vocales", None, "5", "strings", NivelDificultad.BASICO)],
            "codigo_correcto": "palabra = 'murciélago'\nprint(sum(1 for c in palabra if c in 'aeiouáéíóú'))",
        },
        {
            "nombre":      "Palíndromo",
            "descripcion": "Verifica si 'ana' es palíndromo e imprime True. Luego verifica 'luis' e imprime False.",
            "casos": [CasoPrueba("palindromo", None, "True\nFalse", "strings", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "def palindromo(s):\n    return s == s[::-1]\nprint(palindromo('ana'))\nprint(palindromo('luis'))",
        },
    ],
    "condicionales": [
        {
            "nombre":      "Positivo, negativo o cero",
            "descripcion": "Dado x = 7, imprime 'positivo', 'negativo' o 'cero' según corresponda.",
            "casos": [CasoPrueba("positivo", None, "positivo", "condicionales", NivelDificultad.BASICO)],
            "codigo_correcto": "x = 7\nif x > 0:\n    print('positivo')\nelif x < 0:\n    print('negativo')\nelse:\n    print('cero')",
        },
        {
            "nombre":      "Mayor de edad",
            "descripcion": "Dado edad = 20, imprime 'mayor de edad' si es >= 18, si no imprime 'menor de edad'.",
            "casos": [CasoPrueba("mayor edad", None, "mayor de edad", "condicionales", NivelDificultad.BASICO)],
            "codigo_correcto": "edad = 20\nif edad >= 18:\n    print('mayor de edad')\nelse:\n    print('menor de edad')",
        },
    ],
    "diccionarios": [
        {
            "nombre":      "Acceder a clave",
            "descripcion": "Crea un diccionario con clave 'lenguaje' y valor 'Python'. Imprime el valor accediendo por la clave.",
            "casos": [CasoPrueba("valor clave", None, "Python", "diccionarios", NivelDificultad.BASICO)],
            "codigo_correcto": "d = {'lenguaje': 'Python'}\nprint(d['lenguaje'])",
        },
        {
            "nombre":      "Contar frecuencia",
            "descripcion": "Cuenta cuántas veces aparece cada letra en 'hola' e imprime el diccionario.",
            "casos": [CasoPrueba("frecuencia", None, "{'h': 1, 'o': 1, 'l': 1, 'a': 1}", "diccionarios", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "palabra = 'hola'\nfreq = {}\nfor c in palabra:\n    freq[c] = freq.get(c, 0) + 1\nprint(freq)",
        },
    ],
    "recursion": [
        {
            "nombre":      "Fibonacci",
            "descripcion": "Escribe una función recursiva fibonacci(n) e imprime fibonacci(6). Resultado esperado: 8",
            "casos": [CasoPrueba("fibonacci 6", None, "8", "recursion", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\nprint(fibonacci(6))",
        },
        {
            "nombre":      "Suma recursiva",
            "descripcion": "Escribe una función suma_recursiva(n) que sume del 1 al n de forma recursiva. Imprime suma_recursiva(4). Resultado: 10",
            "casos": [CasoPrueba("suma recursiva", None, "10", "recursion", NivelDificultad.INTERMEDIO)],
            "codigo_correcto": "def suma_recursiva(n):\n    if n == 0:\n        return 0\n    return n + suma_recursiva(n-1)\nprint(suma_recursiva(4))",
        },
    ],
    "variables_y_tipos": [
        {
            "nombre":      "Tipos básicos",
            "descripcion": "Declara una variable entera con valor 42 e imprímela.",
            "casos": [CasoPrueba("entero 42", None, "42", "variables_y_tipos", NivelDificultad.BASICO)],
            "codigo_correcto": "x = 42\nprint(x)",
        },
        {
            "nombre":      "Conversión de tipos",
            "descripcion": "Convierte el string '15' a entero, súmale 10 e imprime el resultado. Resultado: 25",
            "casos": [CasoPrueba("conversion", None, "25", "variables_y_tipos", NivelDificultad.BASICO)],
            "codigo_correcto": "texto = '15'\nprint(int(texto) + 10)",
        },
    ],
}


def obtener_ejercicio(concepto: str, indice: int = 0) -> dict:
    """Retorna un ejercicio específico del concepto."""
    ejercicios = EJERCICIOS.get(concepto, [])
    if not ejercicios:
        return None
    return ejercicios[indice % len(ejercicios)]


def obtener_casos(concepto: str, indice: int = 0) -> list:
    """Retorna los casos de prueba de un ejercicio específico."""
    ejercicio = obtener_ejercicio(concepto, indice)
    if not ejercicio:
        return []
    return ejercicio["casos"]


def listar_conceptos() -> list[str]:
    return list(EJERCICIOS.keys())


def listar_ejercicios(concepto: str) -> list[str]:
    """Lista los nombres de todos los ejercicios de un concepto."""
    return [e["nombre"] for e in EJERCICIOS.get(concepto, [])]
