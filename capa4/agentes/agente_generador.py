"""
AGENTE 3 — Generador de Contenido
Capa 4 — Sistema de Tutoría Socrática UPTC

Se activa cuando el Analista detecta una laguna específica.
Genera un ejercicio nuevo calibrado al nivel del estudiante.
Fase 1: plantillas parametrizadas.
"""

import random

PLANTILLAS = {
    "variables_y_tipos": [
        {
            "enunciado": "Declara una variable llamada `{nombre}` con el valor `{valor}` y muestra su tipo con `type()`.",
            "params": [
                {"nombre": "edad", "valor": "25"},
                {"nombre": "precio", "valor": "19.99"},
                {"nombre": "activo", "valor": "True"},
            ],
            "salida_esperada_template": "<class '{tipo}'>",
            "tipos": ["int", "float", "bool"],
            "dificultad": "basico",
        },
        {
            "enunciado": "Convierte el string `\"{valor}\"` a entero y súmale `{suma}`. Imprime el resultado.",
            "params": [
                {"valor": "10", "suma": 5, "resultado": 15},
                {"valor": "42", "suma": 8, "resultado": 50},
            ],
            "dificultad": "basico",
        },
    ],
    "condicionales": [
        {
            "enunciado": "Escribe una función `clasificar(n)` que retorne `'positivo'`, `'negativo'` o `'cero'` según el valor de `n`. Pruébala con `{valor}`.",
            "params": [
                {"valor": "5"},
                {"valor": "-3"},
                {"valor": "0"},
            ],
            "dificultad": "basico",
        },
        {
            "enunciado": "Dado `nota = {nota}`, imprime `'Aprobado'` si es mayor o igual a 60, `'Reprobado'` si no.",
            "params": [
                {"nota": 75},
                {"nota": 45},
                {"nota": 60},
            ],
            "dificultad": "basico",
        },
    ],
    "ciclos": [
        {
            "enunciado": "Usa un ciclo `for` con `range()` para imprimir los múltiplos de `{base}` del 1 al {limite}.",
            "params": [
                {"base": 3, "limite": 30},
                {"base": 5, "limite": 50},
                {"base": 7, "limite": 70},
            ],
            "dificultad": "basico",
        },
        {
            "enunciado": "Usa un ciclo `while` para calcular la suma de los números del 1 al `{n}` sin usar `sum()`.",
            "params": [
                {"n": 10, "resultado": 55},
                {"n": 5, "resultado": 15},
                {"n": 20, "resultado": 210},
            ],
            "dificultad": "intermedio",
        },
    ],
    "funciones": [
        {
            "enunciado": "Escribe una función `{nombre}(x)` que reciba un número y retorne (no imprima) su {operacion}. Pruébala con `{valor}`.",
            "params": [
                {"nombre": "cuadrado", "operacion": "cuadrado (x²)", "valor": 4},
                {"nombre": "triple", "operacion": "triple (x*3)", "valor": 7},
                {"nombre": "negativo", "operacion": "negativo (-x)", "valor": 5},
            ],
            "dificultad": "basico",
        },
    ],
    "listas": [
        {
            "enunciado": "Dada la lista `{lista}`, escribe código que imprima solo los elementos {condicion}.",
            "params": [
                {"lista": "[1, 2, 3, 4, 5, 6]", "condicion": "pares"},
                {"lista": "[10, 3, 7, 1, 9, 4]", "condicion": "mayores que 5"},
                {"lista": "[-2, 0, 3, -1, 5]", "condicion": "positivos"},
            ],
            "dificultad": "intermedio",
        },
    ],
    "strings": [
        {
            "enunciado": "Dado el string `\"{texto}\"`, imprime: 1) su longitud, 2) en mayúsculas, 3) invertido.",
            "params": [
                {"texto": "Python"},
                {"texto": "hola mundo"},
                {"texto": "uptc"},
            ],
            "dificultad": "basico",
        },
    ],
    "diccionarios": [
        {
            "enunciado": "Crea un diccionario `estudiante` con las claves `nombre`, `nota` y `aprobado`. Usa `nota = {nota}` y calcula `aprobado` automáticamente (True si nota >= 60).",
            "params": [
                {"nota": 75},
                {"nota": 45},
                {"nota": 60},
            ],
            "dificultad": "intermedio",
        },
    ],
    "recursion": [
        {
            "enunciado": "Escribe una función recursiva `suma_digitos(n)` que sume los dígitos de un número entero positivo. Por ejemplo, `suma_digitos({ejemplo})` debe retornar `{resultado}`.",
            "params": [
                {"ejemplo": 123, "resultado": 6},
                {"ejemplo": 456, "resultado": 15},
                {"ejemplo": 99,  "resultado": 18},
            ],
            "dificultad": "intermedio",
        },
    ],
}


class AgenteGenerador:
    """
    Agente 3 — Generador de ejercicios calibrados al perfil del estudiante.
    """

    def generar_ejercicio(
        self,
        concepto: str,
        dificultad: str = "basico",
        errores_previos: list = None,
    ) -> dict:
        """
        Genera un ejercicio para el concepto dado.

        Retorna:
        {
            "concepto":    str,
            "dificultad":  str,
            "enunciado":   str,   ← texto del ejercicio listo para mostrar
            "pista":       str,   ← pista inicial socrática
            "salida_esperada": str | None,
        }
        """
        plantillas_concepto = PLANTILLAS.get(concepto, [])
        if not plantillas_concepto:
            return self._ejercicio_generico(concepto)

        # Filtrar por dificultad si es posible
        filtradas = [p for p in plantillas_concepto if p.get("dificultad") == dificultad]
        if not filtradas:
            filtradas = plantillas_concepto

        plantilla = random.choice(filtradas)
        params    = random.choice(plantilla["params"])

        # Formatear el enunciado con los parámetros
        try:
            enunciado = plantilla["enunciado"].format(**params)
        except KeyError:
            enunciado = plantilla["enunciado"]

        pista = self._generar_pista(concepto, dificultad)

        return {
            "concepto":        concepto,
            "dificultad":      dificultad,
            "enunciado":       enunciado,
            "pista":           pista,
            "salida_esperada": str(params.get("resultado", "")),
        }

    def _generar_pista(self, concepto: str, dificultad: str) -> str:
        """Genera una pista socrática inicial para el ejercicio."""
        pistas = {
            "variables_y_tipos": "¿Recuerdas cómo se verifica el tipo de un valor en Python?",
            "condicionales":     "¿Qué estructura de Python te permite ejecutar código solo si se cumple una condición?",
            "ciclos":            "¿Cuántas veces necesita repetirse el bloque de código?",
            "funciones":         "Recuerda que `def` define la función y `return` devuelve el valor — ¿cuál necesitas aquí?",
            "listas":            "¿Cómo accedes a cada elemento de una lista para evaluarlo?",
            "strings":           "Los strings en Python tienen muchos métodos útiles — ¿cuál necesitas para esta operación?",
            "diccionarios":      "¿Cómo se define un par clave:valor en Python?",
            "recursion":         "Toda función recursiva necesita dos partes — ¿cuáles son?",
        }
        return pistas.get(concepto, "¿Por dónde empezarías a resolver este problema?")

    def _ejercicio_generico(self, concepto: str) -> dict:
        return {
            "concepto":        concepto,
            "dificultad":      "basico",
            "enunciado":       f"Escribe un programa en Python que demuestre el uso de {concepto}.",
            "pista":           "¿Qué elementos básicos necesitas para resolver este ejercicio?",
            "salida_esperada": None,
        }
