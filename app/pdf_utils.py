# app/pdf_utils.py
import pdfkit
from io import BytesIO

WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

def render_pdf_from_html(html: str):
    pdf_bytes = pdfkit.from_string(html, False, configuration=config)
    return BytesIO(pdf_bytes)
