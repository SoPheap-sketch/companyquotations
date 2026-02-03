# app/routes/quotes.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import json

from app.db import SessionLocal
from app.models import Quote, QuoteItem, Project
from app.pdf_utils import render_pdf_from_html
from fastapi.responses import StreamingResponse
from app.utils.audit import write_audit_log

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================
# VIEW QUOTE
# =============================
@router.get("/quotes/{quote_id}", response_class=HTMLResponse)
def view_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        return templates.TemplateResponse(
            "quote_view.html",
            {
                "request": request,
                "quote": quote,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()


# =============================
# EDIT QUOTE
# =============================
@router.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
def edit_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        if quote.status == "approved":
            raise HTTPException(
                status_code=403,
                detail="Approved quotes cannot be edited"
            )

        items = db.query(QuoteItem).filter(
            QuoteItem.quote_id == quote_id
        ).all()

        return templates.TemplateResponse(
            "quote_edit.html",
            {
                "request": request,
                "quote": quote,
                "items_json": json.dumps([
                    {
                        "element": i.element or "",
                        "quantity": i.quantity or 0,
                        "unit_price": i.unit_price or 0,
                        "remark": i.remark or "",
                    }
                    for i in items
                ]),
                "project_id": quote.project_id,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()


# =============================
# NEW QUOTE (FROM PROJECT)
# =============================
@router.get("/projects/{project_id}/quotes/new", response_class=HTMLResponse)
def new_quote_form(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(404)

        quote = Quote(
            project_id=project_id,
            title="Draft Estimate",
            status="draft",
            profit_margin=0.30,
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)

        return templates.TemplateResponse(
            "quote_edit.html",
            {
                "request": request,
                "quote": quote,
                "items_json": "[]",
                "project_id": project_id,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()


# =============================
# DELETE QUOTE
# =============================
# @router.post("/quotes/{quote_id}/delete")
# def delete_quote(quote_id: int, next: str = Form(None)):
#     db = SessionLocal()
#     try:
#         quote = db.query(Quote).filter(Quote.id == quote_id).first()
#         if quote:
#             project_id = quote.project_id
#             db.delete(quote)
#             db.commit()
#     finally:
#         db.close()

#     return RedirectResponse(next or f"/projects/{project_id}", status_code=303)
@router.post("/quotes/{quote_id}/delete")
def delete_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            request.session["flash_error"] = "Quote not found."
            return RedirectResponse("/", status_code=303)

        #  BLOCK approved quote
        if quote.status == "approved":
            request.session["flash_error"] = "Approved quotes cannot be deleted."
            return RedirectResponse(
                f"/projects/{quote.project_id}",
                status_code=303
            )

        db.delete(quote)
        db.commit()

        request.session["flash_success"] = "Quote deleted successfully."

        return RedirectResponse(
            f"/projects/{quote.project_id}",
            status_code=303
        )
    finally:
        db.close()


# =============================
# SUBMIT FOR APPROVAL
# =============================
@router.post("/quotes/{quote_id}/submit")
def submit_quote(
    request: Request,
    quote_id: int
):
    # must be logged in
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()

        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        # only draft can be submitted
        if quote.status != "draft":
            raise HTTPException(
                status_code=400,
                detail="Only draft quotes can be submitted"
            )

        # update status
        quote.status = "pending"
        db.commit()
        db.refresh(quote)
        # AUDIT LOG
        write_audit_log(
            request=request,
            action="SUBMIT_QUOTE",
            description=f"Submitted quote #{quote.id} for approval",
            target_user_id=request.session.get("user_id"),
        )
    finally:
        db.close()
    return RedirectResponse(f"/quotes/{quote_id}",status_code=303)
# =============================
# APPROVE QUOTE
# =============================
@router.post("/quotes/{quote_id}/approve")
def approve_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or quote.status != "pending":
            raise HTTPException(400)

        quote.status = "approved"
        db.commit()
        db.refresh(quote)

        write_audit_log(
            request=request,
            action="APPROVE_QUOTE",
            description=f"Approved quote #{quote.id}",
            target_user_id=request.session.get("user_id"),
        )
    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)

@router.post("/quotes/{quote_id}/reject")
def reject_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or quote.status != "pending":
            raise HTTPException(400)

        quote.status = "rejected"
        db.commit()

        write_audit_log(
            request=request,
            action="REJECT_QUOTE",
            description=f"Rejected quote #{quote.id}",
            target_user_id=request.session.get("user_id"),
        )
    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)

# =============================
# PDF EXPORT
# =============================
@router.get("/quotes/{quote_id}/pdf")
def quote_pdf(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        if quote.payment_due is None:
            quote.payment_due = quote.created_at + timedelta(days=30)
            db.commit()
        
        subtotal = 0
        for item in quote.items:
            # Apply profit margin to each unit price, then multiply by quantity
            selling_unit_price = int(item.unit_price * (1 + quote.profit_margin))
            subtotal += selling_unit_price * item.quantity
        
        # 2. Calculate Tax (10%)
        tax = int(subtotal * 0.10)
        
        # 3. Calculate Final Total
        total = subtotal + tax
        html = templates.get_template("quote_pdf.html").render({
            "request": request,
            "quote": quote,
            "items": quote.items,
            "subtotal": subtotal,  
            "tax": tax,
            "total": total,
            "payment_due": quote.payment_due.strftime("%Y/%m/%d"),
        })

        pdf = render_pdf_from_html(html)

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=quote_{quote.id}.pdf"}
        )
    finally:
        db.close()
