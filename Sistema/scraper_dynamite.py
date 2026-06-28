import time
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from deep_translator import GoogleTranslator


CATEGORIAS = {
    "Developer / Engineer": "https://dynamitejobs.com/category/remote-development-jobs",
    "Management / Operations": "https://dynamitejobs.com/category/remote-management-operations-jobs",
}


def traducir(texto):
    try:
        if not texto or texto == "No especificado":
            return texto
        return GoogleTranslator(source="auto", target="es").translate(str(texto)[:1800])
    except:
        return texto


def es_salario_valido(linea):
    texto = linea.lower()

    patrones_salario = [
        r"\$\s?\d{2,3}k\s?[-–]\s?\$?\s?\d{2,3}k",
        r"\$\s?\d{2,3},?\d{3}\s?[-–]\s?\$?\s?\d{2,3},?\d{3}",
        r"\$\s?\d+(\.\d+)?\s?(\/|per)\s?(hour|month|year|yr)",
        r"\d{2,3}k\s?[-–]\s?\d{2,3}k\s?(\/|per)?\s?(year|yr)?",
    ]

    descartes = ["million", "funding", "customers", "revenue", "investment", "raised"]

    if any(p in texto for p in descartes):
        return False

    return any(re.search(patron, texto) for patron in patrones_salario)


def extraer_salario(lineas):
    for linea in lineas:
        if es_salario_valido(linea):
            return linea.strip()
    return "No especificado"


def limpiar_titulo(titulo):
    invalidos = [
        "Dynamite Jobs", "Remote Jobs", "Find a Remote Job",
        "Load More", "Post a job here!", "Login", "Sign Up"
    ]

    if not titulo or titulo.strip() in invalidos:
        return "No encontrado"

    return titulo.strip()


def limpiar_bloque(texto):
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def extraer_requisitos_y_responsabilidades(lineas):
    texto = "\n".join(lineas)

    patrones_requisitos = [
        r"(Requirements|Qualifications|What you bring|What you'll bring|You have|Required skills)(.*?)(Responsibilities|What you'll do|About the role|Benefits|Apply|$)",
    ]

    patrones_responsabilidades = [
        r"(Responsibilities|What you'll do|About the role|The role|Your role)(.*?)(Requirements|Qualifications|Benefits|Apply|$)",
    ]

    requisitos = ""
    responsabilidades = ""

    for patron in patrones_requisitos:
        m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if m:
            requisitos = limpiar_bloque(m.group(2))
            break

    for patron in patrones_responsabilidades:
        m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if m:
            responsabilidades = limpiar_bloque(m.group(2))
            break

    if not requisitos:
        posibles = []
        claves = ["experience", "years", "skills", "knowledge", "familiar", "proficiency", "degree"]
        for linea in lineas:
            if any(c in linea.lower() for c in claves):
                posibles.append(linea)
        requisitos = " ".join(posibles[:8])

    if not responsabilidades:
        responsabilidades = " ".join(lineas[:25])

    if len(requisitos) < 40:
        requisitos = "Requisitos no especificados claramente en la oferta."

    if len(responsabilidades) < 40:
        responsabilidades = "Responsabilidades no especificadas claramente en la oferta."

    return traducir(requisitos), traducir(responsabilidades)


def obtener_links(driver, url_base, cantidad_links=120):
    links = []
    vistos = set()
    pagina = 1

    while len(links) < cantidad_links and pagina <= 10:
        url = url_base if pagina == 1 else f"{url_base}?page={pagina}"
        print("Visitando listado:", url)

        driver.get(url)
        time.sleep(3)

        enlaces = driver.find_elements(By.TAG_NAME, "a")

        for enlace in enlaces:
            href = enlace.get_attribute("href")
            texto = enlace.text.strip()

            if not href:
                continue

            if "/company/" in href and "/remote-job/" in href and href not in vistos:
                titulo = limpiar_titulo(texto)

                if titulo != "No encontrado":
                    vistos.add(href)
                    links.append({
                        "url": href,
                        "titulo_original": titulo
                    })

            if len(links) >= cantidad_links:
                break

        pagina += 1

    return links


def extraer_detalle(driver, oferta, categoria):
    link = oferta["url"]
    titulo_original = limpiar_titulo(oferta["titulo_original"])

    if titulo_original == "No encontrado":
        return None

    driver.get(link)
    time.sleep(2)

    texto = driver.find_element(By.TAG_NAME, "body").text
    lineas = [x.strip() for x in texto.split("\n") if x.strip()]

    salario = extraer_salario(lineas)

    if salario == "No especificado":
        return None

    partes = link.split("/")
    empresa = "No encontrada"

    if "company" in partes:
        empresa = partes[partes.index("company") + 1].replace("-", " ").title()

    requisitos, responsabilidades = extraer_requisitos_y_responsabilidades(lineas)

    return {
        "titulo": traducir(titulo_original),
        "empresa": empresa,
        "categoria": categoria,
        "ubicacion": "Remoto",
        "salario": salario,
        "requisitos": requisitos,
        "responsabilidades": responsabilidades,
        "descripcion": requisitos + " " + responsabilidades,
        "url": link,
        "fuente": "Dynamite Jobs"
    }


def obtener_empleos_todas_categorias(limite_por_categoria=20):
    driver = webdriver.Edge(
        service=Service(EdgeChromiumDriverManager().install())
    )

    empleos = []

    for categoria, url_base in CATEGORIAS.items():
        print("\nCategoría:", categoria)

        ofertas = obtener_links(driver, url_base, cantidad_links=120)

        contador = 0

        for oferta in ofertas:
            if contador >= limite_por_categoria:
                break

            try:
                empleo = extraer_detalle(driver, oferta, categoria)

                if empleo is not None:
                    empleos.append(empleo)
                    contador += 1
                    print("Guardado:", empleo["titulo"], "| Salario:", empleo["salario"])

            except Exception as e:
                print("Error en oferta:", oferta["url"])
                print(e)

        print(f"Total válido en {categoria}: {contador}")

    driver.quit()
    return empleos
