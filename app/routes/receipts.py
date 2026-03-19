from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.db import SessionLocal
from app.models import Invoice
from app.pdf_utils import render_pdf_from_html
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/receipts/{invoice_id}/pdf")
def receipt_pdf(request: Request, invoice_id: int):

    db = SessionLocal()

    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise HTTPException(404)

        # get quote from invoice
        quote = invoice.quote

        issue_date = datetime.now().strftime("%Y/%m/%d")

        html = templates.get_template("receipt_pdf.html").render({
            "request": request,
            "invoice": invoice,
            "quote": quote,              
            "amount": invoice.total,
            "issue_date": issue_date,
            "description": quote.title
        })

        pdf = render_pdf_from_html(html)

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=receipt_{invoice.id}.pdf"
            }
        )

    finally:
        db.close()