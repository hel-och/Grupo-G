import re
import unicodedata


def limpiar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def calcular_riesgo(empleo):
    riesgo = 0
    razones = []

    texto_original = (
        empleo.get("titulo", "") + " " +
        empleo.get("empresa", "") + " " +
        empleo.get("salario", "") + " " +
        empleo.get("descripcion", "")
    )

    texto = limpiar_texto(texto_original)

    reglas = [
        (r"\b(dinero rapido|gana dinero|ingresos garantizados|ganancias garantizadas|easy money|quick money)\b", 35, "Promesa de dinero fácil o ganancias garantizadas"),
        (r"\b(sin experiencia|no necesitas experiencia|no experience required)\b", 20, "Oferta demasiado fácil o sin experiencia requerida"),
        (r"\b(urgente|contratacion inmediata|inicio inmediato|apply now)\b", 15, "Lenguaje de urgencia"),
        (r"\b(whatsapp|telegram|mensaje directo|dm)\b", 25, "Contacto externo poco formal"),
        (r"\b(gmail|hotmail|yahoo|outlook)\.com\b", 25, "Correo no corporativo"),
        (r"\b(pago para postular|pagar capacitacion|deposito previo|inversion inicial|upfront payment)\b", 45, "Solicitud de pago o inversión previa"),
        (r"\b(forex|trading|investment opportunity|oportunidad de inversion|bitcoin investment)\b", 30, "Referencia financiera riesgosa"),
        (r"\b(sin entrevista|aprobacion inmediata|no interview)\b", 25, "Proceso de selección poco confiable"),
    ]

    for patron, puntos, razon in reglas:
        if re.search(patron, texto):
            riesgo += puntos
            razones.append(razon)

    if empleo.get("empresa") in ["", "No encontrada", None]:
        riesgo += 20
        razones.append("Empresa no identificada")

    if len(empleo.get("descripcion", "")) < 150:
        riesgo += 15
        razones.append("Descripción muy corta")

    if riesgo >= 50:
        nivel = "Alto"
    elif riesgo >= 20:
        nivel = "Medio"
    else:
        nivel = "Bajo"

    if not razones:
        razones.append("Sin señales sospechosas relevantes")

    return riesgo, nivel, "; ".join(razones)
