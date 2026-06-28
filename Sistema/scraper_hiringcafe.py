import re
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from deep_translator import GoogleTranslator


URL = "https://hiring.cafe/"
FUENTE = "Hiring Cafe"
CATEGORIA = "Tecnología de la información"


def traducir(texto):
    try:
        if not texto or texto == "No especificado":
            return texto
        return GoogleTranslator(source="auto", target="es").translate(str(texto)[:1800])
    except:
        return texto


def extraer_salario(texto):
    patrones = [
        r"\$\s?\d+(?:\.\d+)?\s*/\s?(?:hr|hour)",
        r"\$\s?\d+k\s*[-–]\s*\$?\d+k\s*/\s?(?:yr|year)",
        r"\$\s?\d+\s*[-–]\s*\$?\d+\s*/\s?(?:yr|year|hr|hour)",
        r"\$\s?\d{1,3}(?:,\d{3})+\s*[-–]\s*\$?\d{1,3}(?:,\d{3})+",
        r"\$\s?\d+k\s*[-–]\s*\$?\d+k",
    ]

    for patron in patrones:
        encontrado = re.search(patron, texto, re.IGNORECASE)
        if encontrado:
            return encontrado.group().replace(" ", "")

    return "No especificado"


def obtener_periodo(salario):
    s = salario.lower()

    if "/hr" in s or "hour" in s:
        return "por hora"

    if "/yr" in s or "year" in s:
        return "por año"

    return "No especificado"


def limpiar_lineas(texto):
    return [x.strip() for x in texto.split("\n") if x.strip()]


def dividir_bloques(texto):
    lineas = limpiar_lineas(texto)
    bloques = []
    bloque_actual = []

    patron_inicio = re.compile(r"^(\d+h|\d+d|\d+w|\d+m)$", re.IGNORECASE)

    for linea in lineas:
        if patron_inicio.match(linea):
            if bloque_actual:
                bloques.append(bloque_actual)
            bloque_actual = [linea]
        else:
            if bloque_actual:
                bloque_actual.append(linea)

    if bloque_actual:
        bloques.append(bloque_actual)

    return bloques


def extraer_empresa(bloque):
    for linea in bloque:
        if ":" in linea:
            empresa = linea.split(":")[0].strip()

            invalidos = [
                "NYSE", "NASDAQ", "XETRA", "Tokyo Stock Exchange",
                "Frankfurt Stock Exchange", "Toronto Stock Exchange"
            ]

            if not any(x.lower() in empresa.lower() for x in invalidos):
                return empresa

    return "No encontrada"


def extraer_ubicacion(bloque):
    if len(bloque) >= 3:
        ubicacion = bloque[2]

        if "$" not in ubicacion and len(ubicacion) > 2:
            return traducir(ubicacion)

    texto = " ".join(bloque).lower()

    if "remote" in texto:
        return "Remoto"

    if "hybrid" in texto:
        return "Híbrido"

    if "onsite" in texto:
        return "Presencial"

    return "Remoto"


def extraer_requisitos_y_responsabilidades(bloque, empresa):
    texto_bloque = " ".join(bloque)

    requisitos = []
    responsabilidades = []

    claves_requisitos = [
        "yoe", "years", "experience", "degree", "bachelor",
        "required", "skills", "knowledge", "proficiency",
        "english", "sql", "python", "aws", "excel"
    ]

    for linea in bloque:
        l = linea.lower()

        if any(c in l for c in claves_requisitos):
            requisitos.append(linea)

    if empresa != "No encontrada":
        for i, linea in enumerate(bloque):
            if linea.startswith(empresa + ":"):
                responsabilidades = bloque[i:i + 5]
                break

    if not responsabilidades:
        responsabilidades = bloque[3:10]

    requisitos_txt = " ".join(requisitos[:8])
    responsabilidades_txt = " ".join(responsabilidades[:8])

    if len(requisitos_txt) < 40:
        requisitos_txt = "Requisitos no especificados claramente en la oferta."

    if len(responsabilidades_txt) < 40:
        responsabilidades_txt = texto_bloque

    return traducir(requisitos_txt), traducir(responsabilidades_txt)


def extraer_empleo_desde_bloque(bloque):
    texto_bloque = " ".join(bloque)
    salario = extraer_salario(texto_bloque)

    if salario == "No especificado":
        return None

    if len(bloque) < 2:
        return None

    titulo = bloque[1]
    empresa = extraer_empresa(bloque)
    ubicacion = extraer_ubicacion(bloque)
    periodo = obtener_periodo(salario)

    salario_final = salario
    if periodo != "No especificado":
        salario_final = f"{salario} {periodo}"

    requisitos, responsabilidades = extraer_requisitos_y_responsabilidades(bloque, empresa)

    return {
        "titulo": traducir(titulo),
        "empresa": empresa,
        "categoria": CATEGORIA,
        "ubicacion": ubicacion,
        "salario": salario_final,
        "requisitos": requisitos,
        "responsabilidades": responsabilidades,
        "descripcion": requisitos + " " + responsabilidades,
        "url": URL,
        "fuente": FUENTE
    }


def aceptar_cookies(driver):
    try:
        botones = driver.find_elements(By.TAG_NAME, "button")

        for boton in botones:
            texto = boton.text.lower().strip()

            if "accept" in texto or "agree" in texto or "aceptar" in texto:
                driver.execute_script("arguments[0].click();", boton)
                time.sleep(1)
                break
    except:
        pass


def obtener_texto_pagina(driver):
    for _ in range(12):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(0.7)

    return driver.find_element(By.TAG_NAME, "body").text


def ir_a_pagina(driver, numero_pagina):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    selectores = [
        f"//button[normalize-space()='{numero_pagina}']",
        f"//a[normalize-space()='{numero_pagina}']",
        f"//*[normalize-space()='{numero_pagina}']"
    ]

    for selector in selectores:
        try:
            elementos = driver.find_elements(By.XPATH, selector)

            for elemento in elementos:
                if elemento.is_displayed():
                    driver.execute_script("arguments[0].click();", elemento)
                    time.sleep(6)
                    return True
        except:
            pass

    return False


def texto_seguro(texto):
    return str(texto).encode("ascii", errors="ignore").decode("ascii")


def obtener_empleos_hiringcafe(limite=15):
    opciones = webdriver.EdgeOptions()
    opciones.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.geolocation": 2
    })

    driver = webdriver.Edge(
        service=Service(EdgeChromiumDriverManager().install()),
        options=opciones
    )

    driver.maximize_window()
    driver.get(URL)
    time.sleep(10)
    aceptar_cookies(driver)

    empleos = []
    vistos = set()
    pagina = 1

    while len(empleos) < limite and pagina <= 10:
        print(f"\nLeyendo página {pagina}")

        texto = obtener_texto_pagina(driver)
        bloques = dividir_bloques(texto)

        print("Bloques detectados:", len(bloques))

        for bloque in bloques:
            if len(empleos) >= limite:
                break

            empleo = extraer_empleo_desde_bloque(bloque)

            if empleo is None:
                continue

            clave = empleo["titulo"] + empleo["empresa"] + empleo["salario"]

            if clave in vistos:
                continue

            vistos.add(clave)
            empleos.append(empleo)

            print(
                "Guardado:",
                texto_seguro(empleo["titulo"]),
                "| Empresa:",
                texto_seguro(empleo["empresa"]),
                "| Salario:",
                empleo["salario"]
            )

        if len(empleos) >= limite:
            break

        pagina += 1

        if not ir_a_pagina(driver, pagina):
            print("No se pudo avanzar a otra página.")
            break

    driver.quit()
    return empleos
