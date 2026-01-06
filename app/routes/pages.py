# app/routes/pages.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json

from app.db import SessionLocal
from app.models import Project, Quote, QuoteItem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ---------------- DASHBOARD ----------------
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    db = SessionLocal()
    try:
        total_projects = db.query(Project).count()

        pending_estimates = (
            db.query(Quote)
            .filter(Quote.status.in_(["draft", "pending"]))
            .count()
        )

        approved_quotes = (
            db.query(Quote)
            .filter(Quote.status == "approved")
            .count()
        )

        recent_projects = (
            db.query(Project)
            .order_by(Project.id.desc())
            .limit(5)
            .all()
        )

        recent_quotes = (
            db.query(Quote)
            .order_by(Quote.id.desc())
            .limit(5)
            .all()
        )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "current_year": datetime.utcnow().year,
                "total_projects": total_projects,
                "pending_estimates": pending_estimates,
                "approved_quotes": approved_quotes,
                "recent_projects": recent_projects,
                "recent_quotes": recent_quotes,
            },
        )
    finally:
        db.close()

# ---------------- PROJECT PAGES ----------------
@router.get("/projects/form", response_class=HTMLResponse)
def project_form(request: Request):
    return templates.TemplateResponse(
        "projects.html",
        {"request": request, "current_year": datetime.utcnow().year},
    )

@router.get("/projects/list", response_class=HTMLResponse)
def project_list(request: Request):
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).all()
        return templates.TemplateResponse(
            "projects_list.html",
            {
                "request": request,
                "projects": projects,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_view(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        quotes = (
            db.query(Quote)
            .filter(Quote.project_id == project_id)
            .order_by(Quote.id.desc())
            .all()
        )

        return templates.TemplateResponse(
            "project_view.html",
            {
                "request": request,
                "project": project,
                "quotes": quotes,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

# ---------------- QUOTE PAGES ----------------
@router.get("/projects/{project_id}/quotes", response_class=HTMLResponse)
def project_quotes(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        quotes = (
            db.query(Quote)
            .filter(Quote.project_id == project_id)
            .order_by(Quote.id.desc())
            .all()
        )
        return templates.TemplateResponse(
            "project_quotes.html",
            {
                "request": request,
                "project": project,
                "quotes": quotes,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

@router.get("/quotes/{quote_id}", response_class=HTMLResponse)
def quote_view(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

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

@router.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
def quote_edit(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        items = (
            db.query(QuoteItem)
            .filter(QuoteItem.quote_id == quote_id)
            .order_by(QuoteItem.id.asc())
            .all()
        )

        items_json = [
            {
                "work_category": i.work_category or "",
                "element": i.element or "",
                "supplier": i.supplier or "",
                "quantity": i.quantity or 0,
                "unit": i.unit or "",
                "unit_price": i.unit_price or 0,
                "remark": i.remark or "",
            }
            for i in items
        ]

        return templates.TemplateResponse(
            "quote_edit.html",
            {
                "request": request,
                "quote": quote,
                "items_json": json.dumps(items_json),
                "project_id": quote.project_id,
            },
        )
    finally:
        db.close()
