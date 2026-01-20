# app/routes/api.py
from fastapi import APIRouter,Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from datetime import timedelta

from app.db import SessionLocal
from app.models import Project, Quote, QuoteItem

from datetime import datetime

router = APIRouter()  
# ---------------- PROJECT ACTIONS ----------------
@router.post("/projects/create")
def create_project(
    client_name: str = Form(...),
    site: str = Form(None),
    contact: str = Form(None),
):
    db = SessionLocal()
    try:
        project = Project(
            client_name=client_name,
            site=site,
            contact=contact
        )
        db.add(project)
        db.commit()
    finally:
        db.close()

    return RedirectResponse("/projects/list", status_code=303)

# ---------------- QUOTE ACTIONS ----------------from fastapi import APIRouter, HTTPException
from app.db import SessionLocal
from app.models import Quote, QuoteItem
from datetime import timedelta

router = APIRouter()

@router.post("/quotes/{quote_id}/items/save")
def save_quote_items(quote_id: int, data: dict):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        if quote.status == "approved":
            raise HTTPException(status_code=403, detail="Approved quotes can't not modified")
        # ===== BASIC INFO =====
        quote.title = data.get("title")
        quote.profit_margin = float(data.get("profit_margin", 0.30))
        # ===== AUTO PAYMENT DUE =====
        if not quote.payment_due:
            quote.payment_due = quote.created_at + timedelta(days=30)
        # ===== RESET ITEMS =====
        db.query(QuoteItem).filter(
            QuoteItem.quote_id == quote_id
        ).delete()
        total_cost = 0
        for item in data.get("items", []):
            qty = float(item.get("quantity", 0))
            price = float(item.get("unit_price", 0))
            amount = qty * price
            total_cost += amount
            db.add(QuoteItem(
                quote_id=quote_id,
                work_category=item.get("work_category"),
                work_type=item.get("work_type"),
                element=item.get("element"),
                supplier=item.get("supplier"),
                quantity=qty,
                unit=item.get("unit"),
                unit_price=price,
                amount=amount,
                spec=item.get("spec"),
                remark=item.get("remark"),
            ))
        # ===== MONEY LOGIC =====
        quote.subtotal = int(total_cost)
        quote.selling_price = int(
            quote.subtotal * (1 + quote.profit_margin)
        )
        quote.tax = int(quote.selling_price * 0.10)
        quote.total = quote.selling_price + quote.tax
        db.commit()
        return {"message": "Saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


