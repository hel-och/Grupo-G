import json
import os

from scraper_dynamite import obtener_empleos_todas_categorias
from scraper_hiringcafe import obtener_empleos_hiringcafe
from detector import calcular_riesgo


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_JSON = os.path.join(BASE_DIR, "empleos.json")


def agregar_riesgo(empleos):
    for empleo in empleos:
        riesgo, nivel, razones = calcular_riesgo(empleo)
        empleo["riesgo"] = riesgo
        empleo["nivel_riesgo"] = nivel
        empleo["razones"] = razones
    return empleos


print("Extrayendo ofertas de Dynamite Jobs...")
empleos_dynamite = obtener_empleos_todas_categorias(limite_por_categoria=20)

print("\nExtrayendo ofertas de Hiring Cafe...")
empleos_hiring = obtener_empleos_hiringcafe(limite=15)

empleos = empleos_dynamite + empleos_hiring

empleos_unicos = []
vistos = set()

for empleo in empleos:
    clave = (
        empleo.get("titulo", "") +
        empleo.get("empresa", "") +
        empleo.get("salario", "") +
        empleo.get("fuente", "")
    )

    if clave not in vistos:
        vistos.add(clave)
        empleos_unicos.append(empleo)

empleos_unicos = agregar_riesgo(empleos_unicos)

with open(RUTA_JSON, "w", encoding="utf-8") as archivo:
    json.dump(empleos_unicos, archivo, ensure_ascii=False, indent=4)

print("\nArchivo empleos.json creado correctamente")
print("Ruta:", RUTA_JSON)
print("Total de ofertas:", len(empleos_unicos))
print("Dynamite Jobs:", len(empleos_dynamite))
print("Hiring Cafe:", len(empleos_hiring))
