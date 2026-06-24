import json
from scraper_dynamite import obtener_empleos_todas_categorias
from detector import calcular_riesgo

empleos = obtener_empleos_todas_categorias(limite_por_categoria=20)

for empleo in empleos:
    riesgo, nivel, razones = calcular_riesgo(empleo)
    empleo["riesgo"] = riesgo
    empleo["nivel_riesgo"] = nivel
    empleo["razones"] = razones

with open("empleos.json", "w", encoding="utf-8") as archivo:
    json.dump(empleos, archivo, ensure_ascii=False, indent=4)

print("Archivo empleos.json creado correctamente")
print("Total de ofertas:", len(empleos))
