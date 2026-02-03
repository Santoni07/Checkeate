import re
import requests
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode


PATRON_CMPC = re.compile(
    r"^[a-f0-9]{32}\s*-\s*CMPC-\d+",
    re.IGNORECASE
)


def validar_qr_data(data: str) -> dict:
    data = data.strip()

    # Caso URL
    if data.startswith("http://") or data.startswith("https://"):
        try:
            resp = requests.head(data, timeout=5, allow_redirects=True)
            return {
                "valido": resp.status_code == 200,
                "tipo": "url",
                "valor": data,
                "status_http": resp.status_code
            }
        except requests.RequestException as e:
            return {
                "valido": False,
                "tipo": "url",
                "valor": data,
                "error": str(e)
            }

    # Caso CMPC (texto)
    if PATRON_CMPC.match(data):
        return {
            "valido": True,
            "tipo": "cmpc",
            "valor": data
        }

    return {
        "valido": False,
        "tipo": "desconocido",
        "valor": data
    }


def extraer_y_validar_qr(file_obj):
    try:
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")

        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            qrs = decode(img)

            for qr in qrs:
                data = qr.data.decode("utf-8")
                resultado = validar_qr_data(data)

                if resultado["valido"]:
                    return resultado

        return {"valido": False, "error": "No se detectó QR válido"}

    except Exception as e:
        return {"valido": False, "error": str(e)}