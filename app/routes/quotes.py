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
@router.post("/quotes/{quote_id}/delete")
def delete_quote(quote_id: int, next: str = Form(None)):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if quote:
            project_id = quote.project_id
            db.delete(quote)
            db.commit()
    finally:
        db.close()

    return RedirectResponse(next or f"/projects/{project_id}", status_code=303)


# =============================
# SUBMIT FOR APPROVAL
# =============================
@router.post("/quotes/{quote_id}/submit")
def submit_quote(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or quote.status != "draft":
            raise HTTPException(400)

        quote.status = "pending"
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)


# =============================
# APPROVE QUOTE
# =============================
@router.post("/quotes/{quote_id}/approve")
def approve_quote(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or quote.status != "pending":
            raise HTTPException(400)

        quote.status = "approved"
        db.commit()
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

        html = templates.get_template("quote_pdf.html").render({
            "request": request,
            "quote": quote,
            "items": quote.items,
            "subtotal": quote.subtotal,
            "tax": quote.tax,
            "total": quote.total,
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
