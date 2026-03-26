# from fastapi import APIRouter, Request, HTTPException
# from fastapi.responses import Response
# from datetime import datetime

# from app.db import SessionLocal
# from app.models import Invoice
# from app.pdf_utils import render_pdf_from_html
# from fastapi.templating import Jinja2Templates

# router = APIRouter()
# templates = Jinja2Templates(directory="app/templates")


# @router.get("/receipts/{invoice_id}/pdf")
# def receipt_pdf(request: Request, invoice_id: int):

#     db = SessionLocal()

#     try:
#         invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

#         if not invoice:
#             raise HTTPException(404)

#         quote = invoice.quote

#         # ===== DATE =====
#         issue_date = datetime.now().strftime("%Y/%m/%d")

#         # ===== AMOUNT CALCULATION =====
#         amount = int(invoice.total or 0)
#         subtotal = int(amount / 1.1)
#         tax = amount - subtotal

#         # ===== RENDER =====
#         html = templates.get_template("receipt_pdf.html").render({
#             "request": request,
#             "invoice": invoice,
#             "quote": quote,
#             "customer_name": quote.project.client_name,
#             "amount": amount,
#             "subtotal": subtotal,
#             "tax": tax,
#             "issue_date": issue_date,
#             "description": quote.title or "工事代金"
#         })

#         pdf = render_pdf_from_html(html)

#         return Response(
#             content=pdf,
#             media_type="application/pdf",
#             headers={
#                 "Content-Disposition": f"inline; filename=receipt_{invoice.id}.pdf"
#             }
#         )

#     finally:
#         db.close()