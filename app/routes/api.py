# app/routes/api.py
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from datetime import timedelta

from app.db import SessionLocal
from app.models import Project, Quote, QuoteItem

router = APIRouter()  # ✅ THIS LINE IS REQUIRED

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

# ---------------- QUOTE ACTIONS ----------------
@router.post("/quotes/{quote_id}/submit")
def submit_quote(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        if quote.status != "draft":
            raise HTTPException(status_code=400, detail="Only draft quotes allowed")

        quote.status = "pending"
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)

@router.post("/quotes/{quote_id}/approve")
def approve_quote(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        if quote.status != "pending":
            raise HTTPException(status_code=400, detail="Only pending quotes allowed")

        quote.status = "approved"
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)
