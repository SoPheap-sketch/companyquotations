

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta

from app.db import SessionLocal
from app.models import Quote, Invoice, Receipt
from fastapi.responses import Response,RedirectResponse
from app.pdf_utils import render_pdf_portrait
from datetime import datetime

from app.db import SessionLocal
from app.models import Invoice

from fastapi.templating import Jinja2Templates

# import pdfkit

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")
@router.post("/quotes/{quote_id}/create-invoice")
def create_invoice(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()

        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        if quote.status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Only approved quotes can create invoice"
            )

        if quote.invoice:
            raise HTTPException(
                status_code=400,
                detail="Invoice already exists"
            )
        invoice = Invoice(
            quote_id=quote.id,
            invoice_number=f"INV-{quote.id}",
            issue_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            subtotal=quote.subtotal,
            tax=quote.tax,
            total=quote.total,
        )
        db.add(invoice)
        db.commit()

    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)

@router.post("/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: int):
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        # mark paid
        invoice.payment_status = "paid"
        invoice.payment_date = datetime.utcnow()

        receipt = Receipt(
            invoice_id=invoice.id,
            receipt_number=f"R-{invoice.id}",
            payment_date=invoice.payment_date,
            payment_method="bank transfer",
            amount_received=invoice.total
        )
        db.add(receipt)
        quote_id = invoice.quote_id
        db.commit()

    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)
@router.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(request: Request, invoice_id: int):

    db = SessionLocal()

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    quote = invoice.quote
    items = quote.items

    # Recalculate totals safely
    profit_margin = quote.profit_margin if quote.profit_margin else 0

    subtotal = sum(
        it.quantity * it.unit_price * (1 + profit_margin)
        for it in items
    )

    subtotal = round(subtotal, 2)
    tax = round(subtotal * 0.10, 2)
    total = round(subtotal + tax, 2)

    html = templates.get_template("invoice_pdf.html").render({
        "request": request,
        "invoice": invoice,
        "quote": quote,
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "payment_due": invoice.due_date.strftime("%Y/%m/%d")
    })

    # config = pdfkit.configuration(
    #     wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    # )

    # pdf = pdfkit.from_string(html, False, configuration=config)
  

    pdf = render_pdf_portrait(html)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=invoice_{invoice_id}.pdf"
        }
    )





@router.get("/receipts/{invoice_id}/pdf")
def receipt_pdf(request: Request, invoice_id: int):

    db = SessionLocal()

    try:
        # ===== GET INVOICE =====
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.payment_status != "paid":
            raise HTTPException(status_code=400, detail="Invoice not paid yet")

        quote = invoice.quote

        # ===== DATE (JAPANESE ERA) =====
        date = invoice.payment_date or datetime.now()

        reiwa_year = date.year - 2018
        year_str = "元" if reiwa_year == 1 else str(reiwa_year)

        issue_date = f"令和{year_str}年{date.month}月{date.day}日"

        # ===== AMOUNT CALCULATION =====
        amount = int(invoice.total or 0)
        subtotal = int(amount / 1.1)
        tax = amount - subtotal

        # ===== CUSTOMER NAME (SAFE) =====
        customer_name = (
            quote.project.client_name
            if quote and quote.project and quote.project.client_name
            else "お客様"
        )

        # ===== DESCRIPTION (SAFE) =====
        description = quote.title if quote and quote.title else "工事代金"

        # ===== RENDER HTML =====
        html = templates.get_template("receipt_pdf.html").render({
            "request": request,
            "invoice": invoice,
            "quote": quote,
            "customer_name": customer_name,
            "amount": amount,
            "subtotal": subtotal,
            "tax": tax,
            "issue_date": issue_date,
            "description": description
        })

        # ===== GENERATE PDF =====
       
        pdf = render_pdf_portrait(html)

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=receipt_{invoice_id}.pdf"
            }
        )

    finally:
        db.close()