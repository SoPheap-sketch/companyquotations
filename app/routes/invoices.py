from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta

from app.db import SessionLocal
from app.models import Quote, Invoice
router = APIRouter()
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