# app/routes/pages.py

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import json

from app.db import SessionLocal

from app.pdf_utils import render_pdf_from_html
from app.services.auth import login_required, admin_required

from app.models import Project, Quote, QuoteItem, User, QuoteApprovalLog
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =====================================================
# DASHBOARD
# =====================================================
@router.get("/", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def dashboard(request: Request):
    db = SessionLocal()
    try:
        total_projects = db.query(Project).count()
        pending_estimates = db.query(Quote).filter(Quote.status == "pending").count()
        approved_quotes = db.query(Quote).filter(Quote.status == "approved").count()

        recent_projects = (
            db.query(Project)
            .order_by(Project.created_at.desc())
            .limit(5)
            .all()
        )

        recent_quotes = (
            db.query(Quote)
            .order_by(Quote.created_at.desc())
            .limit(5)
            .all()
        )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "total_projects": total_projects,
                "pending_estimates": pending_estimates,
                "approved_quotes": approved_quotes,
                "recent_projects": recent_projects,
                "recent_quotes": recent_quotes,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()
# =====================================================
# PROJECTS
# =====================================================
@router.get("/projects/list", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def projects_list(request: Request):
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

@router.get("/projects/form", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def project_form(request: Request):
    return templates.TemplateResponse(
        "projects.html",
        {"request": request, "current_year": datetime.utcnow().year},
    )
@router.post("/projects/create", dependencies=[Depends(login_required)])
def create_project(
    client_name: str = Form(...),
    site: str = Form(None),
    contact: str = Form(None),
):
    db = SessionLocal()
    try:
        db.add(Project(client_name=client_name, site=site, contact=contact))
        db.commit()
    finally:
        db.close()

    return RedirectResponse("/projects/list", status_code=303)

@router.get("/projects/{project_id}", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def view_project(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(404)

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
                "created_at": project.created_at.strftime("%Y-%m-%d"),
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

@router.get("/projects/{project_id}/edit", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def edit_project_form(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(404)

        return templates.TemplateResponse(
            "project_edit.html",
            {
                "request": request,
                "project": project,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

@router.post("/projects/{project_id}/edit", dependencies=[Depends(login_required)])
def edit_project_submit(
    project_id: int,
    client_name: str = Form(...),
    site: str = Form(None),
    contact: str = Form(None),
):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(404)

        project.client_name = client_name
        project.site = site
        project.contact = contact
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f"/projects/{project_id}", status_code=303)
@router.post("/projects/{project_id}/delete", dependencies=[Depends(login_required)])
def delete_project(project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            db.delete(project)
            db.commit()
    finally:
        db.close()

    return RedirectResponse("/projects/list", status_code=303)
# =====================================================
# NEW QUOTE
# =====================================================
@router.get("/projects/{project_id}/quotes/new", response_class=HTMLResponse, dependencies=[Depends(login_required)])
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
# =====================================================
# QUOTES
# =====================================================
@router.get("/quotes/{quote_id}", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def view_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).all()
        approval_logs = (
            db.query(QuoteApprovalLog)
            .filter(QuoteApprovalLog.quote_id == quote_id)
            .order_by(QuoteApprovalLog.created_at.asc())
            .all()
        )

        return templates.TemplateResponse(
            "quote_view.html",
            {
                "request": request,
                "quote": quote,
                "items": items,
                "approval_logs": approval_logs,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

@router.get("/quotes/{quote_id}/edit", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def edit_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)
        if quote.status == "approved":
            raise HTTPException(403, "Approved quotes cannot be edited")
        items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).all()

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
                    } for i in items
                ]),
                "project_id": quote.project_id,
            },
        )
    finally:
        db.close()
@router.post("/quotes/{quote_id}/delete", dependencies=[Depends(login_required)])
def delete_quote(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if quote:
            project_id = quote.project_id
            db.delete(quote)
            db.commit()
            return RedirectResponse(f"/projects/{project_id}", status_code=303)
    finally:
        db.close()
    raise HTTPException(404)


@router.get("/quotes/{quote_id}/pdf", dependencies=[Depends(login_required)])
def quote_pdf(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        if quote.payment_due is None:
            quote.payment_due = quote.created_at + timedelta(days=30)
            db.commit()
            db.refresh(quote)

        pdf = render_pdf_from_html(
            templates.get_template("quote_pdf.html").render({
                "request": request,
                "quote": quote,
                "items": quote.items,
                "subtotal": quote.subtotal,
                "tax": quote.tax,
                "total": quote.total,
                "payment_due": quote.payment_due.strftime("%Y/%m/%d"),
            })
        )

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=quote_{quote.id}.pdf"},
        )
    finally:
        db.close()




