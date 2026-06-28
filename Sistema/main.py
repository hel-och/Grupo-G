import os
import pandas as pd

from scraper_hiringcafe import obtener_empleos_hiringcafe
from scraper_dynamite import obtener_empleos_todas_categorias
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


print("Extrayendo ofertas de Hiring Cafe...")
empleos_hiring = obtener_empleos_hiringcafe(limite=15)

print("\nExtrayendo ofertas de Dynamite Jobs...")
empleos_dynamite = obtener_empleos_todas_categorias(limite_por_categoria=20)

empleos = empleos_hiring + empleos_dynamite

empleos = agregar_riesgo(empleos)

df = pd.DataFrame(empleos)

df = df.drop_duplicates(
    subset=["titulo", "empresa", "salario", "fuente"],
    keep="first"
)

columnas_texto = [
    "titulo", "empresa", "categoria", "ubicacion", "salario",
    "requisitos", "responsabilidades", "descripcion",
    "fuente", "url", "nivel_riesgo", "razones"
]

for columna in columnas_texto:
    if columna not in df.columns:
        df[columna] = ""

df["empresa"] = df["empresa"].replace("", pd.NA).fillna("No encontrada")
df["ubicacion"] = df["ubicacion"].replace("", pd.NA).fillna("Remoto")
df["categoria"] = df["categoria"].replace("", pd.NA).fillna("Sin categoría")
df["salario"] = df["salario"].replace("", pd.NA).fillna("No especificado")

df["requisitos"] = df["requisitos"].replace("", pd.NA).fillna(
    "Requisitos no especificados claramente en la oferta."
)

df["responsabilidades"] = df["responsabilidades"].replace("", pd.NA).fillna(
    "Responsabilidades no especificadas claramente en la oferta."
)

df["descripcion"] = df["requisitos"] + " " + df["responsabilidades"]

print("\nAnálisis con pandas")

print("\nOfertas por fuente:")
print(df["fuente"].value_counts())

print("\nOfertas por categoría:")
print(df["categoria"].value_counts())

print("\nOfertas por nivel de riesgo:")
print(df["nivel_riesgo"].value_counts())

df.to_json(
    RUTA_JSON,
    orient="records",
    force_ascii=False,
    indent=4
)

print("\nArchivo empleos.json creado correctamente")
print("Ruta:", RUTA_JSON)
print("Total de ofertas:", len(df))
print("Hiring Cafe:", len(empleos_hiring))
print("Dynamite Jobs:", len(empleos_dynamite))
