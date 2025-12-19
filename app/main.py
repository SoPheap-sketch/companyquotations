# app/main.py
# Import the database session
from app.db import SessionLocal  

# Import your models
from app.models import Quote, QuoteItem

# Make sure you also have this for the error handling
from fastapi import HTTPException
from fastapi import FastAPI, Request, Form, Body, HTTPException
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    PlainTextResponse
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app import db as _db
import json



app = FastAPI(title="Company Quotation System (MVP)")

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------
# Startup: Initialize DB
# --------------------------------------------------
@app.on_event("startup")
def startup_event():
    _db.init_db()


# --------------------------------------------------
# Homepage
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Quotation Dashboard",
            "current_year": datetime.utcnow().year,
        },
    )

# --------------------------------------------------
# Create Project (POST)
# --------------------------------------------------
@app.post("/projects/create")
def create_project(
    request: Request,
    client_name: str = Form(...),
    site: str = Form(None),
    contact: str = Form(None),
):
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        proj = Project(client_name=client_name, site=site, contact=contact)
        db.add(proj)
        db.commit()
        db.refresh(proj)
    finally:
        db.close()

    return RedirectResponse(url="/projects/list", status_code=303)


# --------------------------------------------------
# Projects JSON API
# --------------------------------------------------
@app.get("/projects", response_class=JSONResponse)
def list_projects():
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).all()
        data = [
            {
                "id": p.id,
                "client_name": p.client_name,
                "site": p.site,
                "contact": p.contact,
            }
            for p in projects
        ]
        return JSONResponse(content=data)
    finally:
        db.close()


# --------------------------------------------------
# Project Create Form (HTML)
# --------------------------------------------------
@app.get("/projects/form", response_class=HTMLResponse)
def projects_form(request: Request):
    return templates.TemplateResponse(
        "projects.html",
        {
            "request": request,
            "current_year": datetime.utcnow().year,
        },
    )


# --------------------------------------------------
# Projects List (HTML)
# --------------------------------------------------
@app.get("/projects/list", response_class=HTMLResponse)
def projects_list(request: Request):
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).all()
    finally:
        db.close()

    return templates.TemplateResponse(
        "projects_list.html",
        {
            "request": request,
            "projects": projects,
            "current_year": datetime.utcnow().year,
        },
    )


# --------------------------------------------------
# DEBUG ROUTE — Helps find internal error
# REMOVE AFTER FIXING
# --------------------------------------------------
@app.get("/projects/debug", response_class=PlainTextResponse)
def projects_debug():
    try:
        from app.db import SessionLocal
        from app.models import Project

        db = SessionLocal()
        try:
            projects = db.query(Project).order_by(Project.id.desc()).all()
            return f"OK — projects count: {len(projects)}"
        finally:
            db.close()
    except Exception:
        import traceback
        return PlainTextResponse(traceback.format_exc(), status_code=500)


# ---------------- View Project ----------------
@app.get("/projects/{project_id}", response_class=HTMLResponse)
def view_project(request: Request, project_id: int):
    from app.db import SessionLocal
    from app.models import Project, Quote
    from datetime import datetime

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

        created_dt = getattr(project, "created_at", None)
        created_str = created_dt.strftime("%Y-%m-%d") if created_dt else None

        return templates.TemplateResponse(
            "project_view.html",
            {
                "request": request,
                "project": project,
                "quotes": quotes,          # ✅ now guaranteed
                "created_at": created_str,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()


# ---------------- Edit Project (GET) ----------------
@app.get("/projects/{project_id}/edit", response_class=HTMLResponse)
def edit_project_form(request: Request, project_id: int):
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return templates.TemplateResponse(
                "project_edit.html",
                {"request": request, "project": None, "error": "Project not found", "current_year": datetime.utcnow().year},
            )
        return templates.TemplateResponse(
            "project_edit.html",
            {"request": request, "project": proj, "current_year": datetime.utcnow().year},
        )
    finally:
        db.close()


# ---------------- Edit Project (POST) ----------------
@app.post("/projects/{project_id}/edit")
def edit_project_submit(
    request: Request,
    project_id: int,
    client_name: str = Form(...),
    site: str = Form(None),
    contact: str = Form(None),
):
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            db.close()
            return RedirectResponse(url="/projects/list", status_code=303)
        proj.client_name = client_name
        proj.site = site
        proj.contact = contact
        db.add(proj)
        db.commit()
        db.refresh(proj)
    finally:
        db.close()

    # After successful edit, go to view page
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


# ---------------- Delete confirm (GET) ----------------
@app.get("/projects/{project_id}/delete", response_class=HTMLResponse)
def delete_project_confirm(request: Request, project_id: int):
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        return templates.TemplateResponse(
            "project_delete_confirm.html",
            {"request": request, "project": proj, "current_year": datetime.utcnow().year},
        )
    finally:
        db.close()


# ---------------- Delete (POST) ----------------
@app.post("/projects/{project_id}/delete")
def delete_project(project_id: int):
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            db.delete(proj)
            db.commit()
    finally:
        db.close()

    return RedirectResponse(url="/projects/list", status_code=303)


# ==================================================
# Quotes: Project-level and Quote-level routes
# ==================================================

# --- Quotes list for a project (HTML) ---
@app.get("/projects/{project_id}/quotes", response_class=HTMLResponse)
def project_quotes(request: Request, project_id: int):
    from app.db import SessionLocal
    from app.models import Quote, Project

    db = SessionLocal()
    try:
        # optional: load project for header
        project = db.query(Project).filter(Project.id == project_id).first()
        quotes = db.query(Quote).filter(Quote.project_id == project_id).order_by(Quote.version.asc(), Quote.id.desc()).all()
        return templates.TemplateResponse(
            "project_quotes.html",
            {"request": request, "project": project, "project_id": project_id, "quotes": quotes, "current_year": datetime.utcnow().year},
        )
    finally:
        db.close()


# --- New Quote form (GET) ---
@app.get("/projects/{project_id}/quotes/new", response_class=HTMLResponse)
def new_quote_form(request: Request, project_id: int):
    from app.db import SessionLocal
    from app.models import Project, Quote

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return templates.TemplateResponse(
                "quote_edit.html",
                {
                    "request": request,
                    "quote": None,
                    "error": "Project not found",
                    "current_year": datetime.utcnow().year,
                },
            )

        # 🔥 CREATE DRAFT QUOTE
        quote = Quote(
            project_id=project_id,
            status="draft",
            profit_margin=0.30,
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)  # 🔥 THIS IS CRITICAL

        return templates.TemplateResponse(
            "quote_edit.html",
            {
                "request": request,
                "quote": quote,  # ✅ REAL QUOTE WITH ID
                "project_id": project.id,
                "project_client_name": project.client_name,
                "items": [],
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()



# --- Create quote (POST) ---
@app.post("/projects/{project_id}/quotes/create")
def create_quote(request: Request, project_id: int):
    from app.db import SessionLocal
    from app.models import Quote

    db = SessionLocal()
    try:
        q = Quote(
            project_id=project_id,
            title="Draft Estimate",   # ✅ AUTO TITLE
            version=1,
            profit_margin=0.30,
            status="draft"
        )
        db.add(q)
        db.commit()
        db.refresh(q)

        return RedirectResponse(
            url=f"/quotes/{q.id}/edit",
            status_code=303
        )
    finally:
        db.close()



# --- View quote (HTML) ---
@app.get("/quotes/{quote_id}", response_class=HTMLResponse)
def view_quote(request: Request, quote_id: int):
    from app.db import SessionLocal
    from app.models import Quote

    db = SessionLocal()
    try:
        q = db.query(Quote).filter(Quote.id == quote_id).first()
        if not q:
            return templates.TemplateResponse("quote_view.html", {"request": request, "quote": None, "error": "Quote not found", "current_year": datetime.utcnow().year})
        return templates.TemplateResponse("quote_view.html", {"request": request, "quote": q, "current_year": datetime.utcnow().year})
    finally:
        db.close()

# --- Edit quote (GET) ---
@app.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
def edit_quote_get(request: Request, quote_id: int):
    from app.db import SessionLocal
    from app.models import Quote, QuoteItem, Project

    db = SessionLocal()
    try:
        q = db.query(Quote).filter(Quote.id == quote_id).first()
        if not q:
            raise HTTPException(status_code=404, detail="Quote not found")

        items = (
            db.query(QuoteItem)
            .filter(QuoteItem.quote_id == quote_id)
            .order_by(QuoteItem.id.asc())
            .all()
        )
        
        project = db.query(Project).filter(Project.id == q.project_id).first()

        # Format items for JavaScript
        items_list = []
        for i in items:
            items_list.append({
                "work_category": i.work_category or "",
                "element": i.element or "",
                "supplier": i.supplier or "",
                "date": i.date or "",
                "spec": i.spec or "",
                "quantity": i.quantity or 0,
                "unit": i.unit or "",
                "unit_price": i.unit_price or 0,
                "remark": i.remark or ""
            })

        return templates.TemplateResponse(
            "quote_edit.html",
            {
                "request": request,
                "quote": q,
                "items_json": json.dumps(items_list), # Crucial for JS loading
                "project_id": q.project_id,
                "project_client_name": project.client_name if project else "N/A",
            }
        )
    finally:
        db.close()
# --- Save quote items (POST JSON) endpoint used by JS from the quote_edit page ---
@app.post("/quotes/{quote_id}/items/save")
def save_quote_items(quote_id: int, data: dict):
    # Now that SessionLocal is imported at the top, this will work
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        quote.title = data.get("title")
        quote.profit_margin = float(data.get("profit_margin", 0.3))

        # Delete old items
        db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).delete()

        total_cost = 0
        for item in data.get("items", []):
            qty = float(item.get("quantity", 0))
            price = float(item.get("unit_price", 0))
            row_sum = qty * price
            total_cost += row_sum

            # Now that QuoteItem is imported at the top, this will work
            new_item = QuoteItem(
                quote_id=quote_id,
                work_category=item.get("work_category"),
                work_type=item.get("work_type"), 
                element=item.get("element"),
                supplier=item.get("supplier"),
                quantity=qty,
                unit=item.get("unit"),
                unit_price=price,
                amount=row_sum,
                spec=item.get("spec"),
                remark=item.get("remark")
            )
            db.add(new_item)
        
        quote.subtotal = total_cost
        quote.total = total_cost * (1 + quote.profit_margin)
        
        db.commit()
        return {"message": "Saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
# --- Delete quote (POST) ---
@app.post("/quotes/{quote_id}/delete")
def delete_quote(request: Request, quote_id: int, next: str = Form(None)):
    from app.db import SessionLocal
    from app.models import Quote

    db = SessionLocal()
    try:
        q = db.query(Quote).filter(Quote.id == quote_id).first()
        if q:
            project_id = q.project_id
            db.delete(q)
            db.commit()
    finally:
        db.close()
    if next:
        return RedirectResponse(next, status_code=303)

    return RedirectResponse(
        url=f"/projects/{project_id}/quotes",
        status_code=303
    )
