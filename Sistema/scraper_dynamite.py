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
        return GoogleTranslator(source="auto", target="es").translate(texto[:1800])
    except:
        return texto


def es_salario_valido(linea):
    texto = linea.lower()

    patrones_salario = [
        r"\$\s?\d{2,3}k\s?[-–]\s?\$?\s?\d{2,3}k",
        r"\$\s?\d{2,3},?\d{3}\s?[-–]\s?\$?\s?\d{2,3},?\d{3}",
        r"usd\s?\d{2,3}k\s?[-–]\s?usd?\s?\d{2,3}k",
        r"\$\s?\d+(\.\d+)?\s?(\/|per)\s?(hour|month|year|yr)",
        r"\$\s?\d{2,3}k\s?(\/|per)\s?(year|yr)",
        r"\d{2,3}k\s?[-–]\s?\d{2,3}k\s?(\/|per)?\s?(year|yr)?",
    ]

    palabras_salario = [
        "per year",
        "per month",
        "per hour",
        "/year",
        "/month",
        "/hour",
        "annually",
        "annual",
        "salary",
        "compensation"
    ]

    palabras_descartar = [
        "million",
        "millions",
        "billion",
        "funding",
        "raised",
        "backed by",
        "customers",
        "databases",
        "revenue",
        "investment"
    ]

    if any(p in texto for p in palabras_descartar):
        return False

    tiene_patron = any(re.search(patron, texto) for patron in patrones_salario)
    tiene_contexto = any(palabra in texto for palabra in palabras_salario)

    return tiene_patron or ("$" in texto and tiene_contexto)


def extraer_salario(lineas):
    for linea in lineas:
        linea_limpia = linea.strip()

        if es_salario_valido(linea_limpia):
            return linea_limpia

    return "No especificado"


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
                vistos.add(href)
                links.append({
                    "url": href,
                    "titulo_original": texto
                })

            if len(links) >= cantidad_links:
                break

        pagina += 1

    return links


def limpiar_titulo(titulo):
    if not titulo:
        return "No encontrado"

    invalidos = [
        "Dynamite Jobs",
        "Remote Jobs",
        "Find a Remote Job",
        "Load More",
        "Post a job here!",
        "For Employers",
        "Login",
        "Sign Up",
        "Subscribe to Job Alerts",
        "Trabajos de dinamita",
        "¡Publica un trabajo aquí!"
    ]

    if titulo.strip() in invalidos:
        return "No encontrado"

    return titulo.strip()


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

    descripcion = " ".join(lineas[:70])

    return {
        "titulo": traducir(titulo_original),
        "empresa": empresa,
        "categoria": categoria,
        "ubicacion": "Remoto",
        "salario": salario,
        "descripcion": traducir(descripcion),
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
