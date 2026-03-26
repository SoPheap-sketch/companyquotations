# import pdfkit

# def render_pdf_from_html(html, output_path):
#     pdfkit.from_string(html, output_path)
# from weasyprint import HTML
# from io import BytesIO

# def render_pdf_from_html(html_content):
#     pdf_io = BytesIO()
#     HTML(string=html_content).write_pdf(pdf_io)
#     pdf_io.seek(0)
#     return pdf_io

# import pdfkit
# from io import BytesIO
# import os

# def render_pdf_from_html(html_content):
#     wkhtml_path = os.getenv("WKHTMLTOPDF_PATH")

#     config = pdfkit.configuration(wkhtmltopdf=wkhtml_path) if wkhtml_path else None

#     pdf_bytes = pdfkit.from_string(html_content, False, configuration=config)
#     return BytesIO(pdf_bytes)

# import pdfkit
# import os

# def render_pdf_from_html(html_content):
#     config = pdfkit.configuration(
#         wkhtmltopdf=os.getenv("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")
#     )
#     pdf = pdfkit.from_string(html_content, False, configuration=config)
#     return pdf

# import pdfkit
# import os

# def render_pdf_from_html(html_content):
#     config = pdfkit.configuration(
#         wkhtmltopdf=os.getenv("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")
#     )
#     pdf = pdfkit.from_string(html_content, False, configuration=config)
#     return pdf

# import os
# import platform
# import pdfkit

# def render_pdf_from_html(html):
#     config = pdfkit.configuration(
#         wkhtmltopdf="/usr/bin/wkhtmltopdf"
#     )

#     options = {
#         "enable-local-file-access": None,
#         "encoding": "UTF-8"
#     }

#     return pdfkit.from_string(html, False, options=options, configuration=config)
import os
import platform
import pdfkit

def render_pdf_from_html(html):

    # Detect OS
    if platform.system() == "Windows":
        wkhtml_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    else:
        wkhtml_path = "/usr/bin/wkhtmltopdf"

    config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)

    options = {
        "enable-local-file-access": None,
        "encoding": "UTF-8"
    }

    return pdfkit.from_string(
        html,
        False,
        options=options,
        configuration=config
    )