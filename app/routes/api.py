# app/routes/api.py
from fastapi import APIRouter,Request, Form, HTTPException
from datetime import timedelta
from app.db import SessionLocal
from app.models import  Quote, QuoteItem
from app.utils.audit import write_audit_log
router = APIRouter()  
# ---------------- PROJECT ACTIONS ----------------
# @router.post("/projects/create")
# def create_project(
#     client_name: str = Form(...),
#     site: str = Form(None),
#     contact: str = Form(None),
# ):
#     db = SessionLocal()
#     try:
#         project = Project(
#             client_name=client_name,
#             site=site,
#             contact=contact
#         )
#         db.add(project)
#         db.commit()
#     finally:
#         db.close()

#     return RedirectResponse("/projects/list", status_code=303)

# ---------------- QUOTE ACTIONS ----------------from fastapi import APIRouter, HTTPException
@router.post("/quotes/{quote_id}/items/save")
def save_quote_items(
    request: Request,
    quote_id: int,
    data: dict
):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        if quote.status == "approved":
            raise HTTPException(
                status_code=403,
                detail="Approved quotes cannot be modified"
            )

        # ===== BASIC INFO =====
        quote.title = data.get("title", quote.title)
        margin = float(data.get("profit_margin", 0.30))
        quote.profit_margin = margin

        # ===== RESET ITEMS =====
        db.query(QuoteItem).filter(
            QuoteItem.quote_id == quote_id
        ).delete()

        original_cost = 0.0

        for item in data.get("items", []):
            qty = float(item.get("quantity", 0))
            price = float(item.get("unit_price", 0))
            amount = qty * price

            original_cost += amount

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

        # ===== TOTAL CALCULATION (CRITICAL) =====
        selling_price = original_cost * (1 + margin)
        tax = selling_price * 0.10

        quote.subtotal = int(original_cost)
        quote.tax = int(tax)
        quote.total = int(selling_price + tax)

        db.commit()

        write_audit_log(
            request=request,
            action="UPDATE_QUOTE",
            description=f"Updated quote #{quote.id}",
            target_user_id=request.session.get("user_id"),
        )

        return {
            "message": "Saved successfully",
            "subtotal": quote.subtotal,
            "tax": quote.tax,
            "total": quote.total,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
