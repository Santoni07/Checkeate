from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os


def convertir_a_pdf(file):
    """
    Recibe un archivo (InMemoryUploadedFile)
    Devuelve un ContentFile en formato PDF
    """

    # Abrir imagen
    image = Image.open(file)

    # Convertir a RGB si hace falta
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Crear PDF en memoria
    buffer = BytesIO()
    image.save(buffer, format="PDF")
    buffer.seek(0)

    nombre_base, _ = os.path.splitext(file.name)
    nombre_pdf = f"{nombre_base}.pdf"

    return ContentFile(buffer.read(), name=nombre_pdf)
