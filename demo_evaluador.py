"""
demo_evaluador.py — Prueba interactiva de la Capa 3 en terminal
Ejecutar: python demo_evaluador.py

Permite escribir código Python directamente en la terminal
y ver el JSON estructurado que retorna el evaluador.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from core.evaluador import EvaluadorPython, CasoPrueba, NivelDificultad
from casos_de_prueba.repositorio import obtener_casos, listar_conceptos

VERDE    = "\033[92m"
ROJO     = "\033[91m"
AMARILLO = "\033[93m"
CYAN     = "\033[96m"
RESET    = "\033[0m"
NEGRITA  = "\033[1m"
DIM      = "\033[2m"

evaluador = EvaluadorPython(timeout_seg=5)

COLORES_TIPO = {
    "correcto":       VERDE,
    "error_sintaxis": AMARILLO,
    "error_runtime":  ROJO,
    "error_logico":   CYAN,
    "error_timeout":  ROJO,
    "error_seguridad": AMARILLO,
}

def separador(titulo=""):
    ancho = 55
    if titulo:
        print(f"\n{DIM}{'─' * 3} {titulo} {'─' * (ancho - len(titulo) - 5)}{RESET}")
    else:
        print(f"{DIM}{'─' * ancho}{RESET}")

def imprimir_resultado(r):
    color = COLORES_TIPO.get(r.tipo_error.value, RESET)
    separador("RESULTADO")
    print(f"  Tipo de error : {color}{NEGRITA}{r.tipo_error.value}{RESET}")
    print(f"  Concepto      : {r.concepto}")
    print(f"  Intento #     : {r.intento_numero}")
    print(f"  Tiempo        : {r.tiempo_total_ms} ms")
    if r.linea_error:
        print(f"  Línea         : {r.linea_error}")

    separador("MENSAJE TÉCNICO")
    print(f"  {r.mensaje_tecnico}")

    if r.casos_ejecutados > 0:
        separador("CASOS DE PRUEBA")
        for caso in r.resultados_casos:
            sym = f"{VERDE}✓{RESET}" if caso.paso else f"{ROJO}✗{RESET}"
            print(f"  {sym} {caso.descripcion}")
            if not caso.paso:
                print(f"      Esperado : {caso.salida_esperada!r}")
                print(f"      Obtenido : {caso.salida_obtenida!r}")

    separador("PREGUNTA SOCRÁTICA")
    print(f"  {CYAN}❓ {r.sugerencia_socratica}{RESET}")

    separador("JSON ESTRUCTURADO")
    d = r.to_dict()
    print(json.dumps(d, indent=2, ensure_ascii=False))

def leer_codigo_multilinea():
    """Lee código multilínea hasta que el usuario escribe 'FIN' solo en una línea."""
    print(f"\n{DIM}Escribe tu código Python (escribe FIN en una línea vacía para terminar):{RESET}")
    lineas = []
    while True:
        try:
            linea = input()
            if linea.strip() == "FIN":
                break
            lineas.append(linea)
        except EOFError:
            break
    return "\n".join(lineas)

def menu_principal():
    conceptos = listar_conceptos()

    print(f"\n{NEGRITA}Sistema de Tutoría Socrática — UPTC{RESET}")
    print(f"{DIM}Capa 3: Evaluador de código Python{RESET}")

    while True:
        separador("MENÚ")
        print("  1. Evaluar código libre")
        print("  2. Evaluar contra casos de prueba del repositorio")
        print("  3. Correr suite de tests automáticos")
        print("  4. Ver conceptos disponibles")
        print("  0. Salir")

        opcion = input(f"\n{NEGRITA}Opción: {RESET}").strip()

        if opcion == "0":
            print("\nHasta luego.\n")
            break

        elif opcion == "1":
            print(f"\n{DIM}Escribe cualquier código Python — solo detecta errores, sin casos de prueba.{RESET}")
            concepto = input(f"Etiqueta de concepto (Enter = general): ").strip() or "general"
            intento  = input("Número de intento [1]: ").strip()
            intento  = int(intento) if intento.isdigit() else 1

            codigo = leer_codigo_multilinea()
            if not codigo.strip():
                print(f"{ROJO}No ingresaste código.{RESET}")
                continue

            # Caso vacío: solo detecta sintaxis y runtime, no compara salida
            casos = [CasoPrueba("ejecución libre", None, "", concepto)]
            resultado = evaluador.evaluar(codigo, casos, concepto, intento)

            # Si corrió sin errores, marcar como correcto independiente de la salida
            if resultado.tipo_error.value == "error_logico" and resultado.casos_pasados == 0:
                from core.evaluador import TipoError, SUGERENCIAS_SOCRATICAS
                import random
                resultado.tipo_error = TipoError.CORRECTO
                resultado.mensaje_tecnico = "El código se ejecutó sin errores."
                resultado.sugerencia_socratica = random.choice(SUGERENCIAS_SOCRATICAS[TipoError.CORRECTO])
                resultado.resultados_casos = []

            imprimir_resultado(resultado)

        elif opcion == "2":
            print(f"\nConceptos disponibles: {', '.join(conceptos)}")
            concepto = input("Concepto: ").strip()
            casos = obtener_casos(concepto)
            if not casos:
                print(f"{ROJO}Concepto no encontrado.{RESET}")
                continue

            codigo = leer_codigo_multilinea()
            if not codigo.strip():
                continue

            intento = input("Número de intento [1]: ").strip()
            intento = int(intento) if intento.isdigit() else 1

            resultado = evaluador.evaluar(codigo, casos, concepto, intento)
            imprimir_resultado(resultado)

        elif opcion == "3":
            print(f"\n{AMARILLO}Corriendo suite de tests...{RESET}\n")
            import subprocess
            ruta_tests = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "test_evaluador.py")
            subprocess.run([sys.executable, ruta_tests])

        elif opcion == "4":
            print(f"\nConceptos en el repositorio:")
            for c in conceptos:
                casos = obtener_casos(c)
                print(f"  • {c} ({len(casos)} casos de prueba)")

        else:
            print(f"{ROJO}Opción no válida.{RESET}")

if __name__ == "__main__":
    menu_principal()
