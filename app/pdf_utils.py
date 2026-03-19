import pdfkit

def render_pdf_from_html(html, output_path):
    pdfkit.from_string(html, output_path)