# app/main.py
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app import db as _db

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
    from app.models import Project
    from datetime import datetime

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return templates.TemplateResponse(
                "project_view.html",
                {"request": request, "project": None, "error": "Project not found", "current_year": datetime.utcnow().year},
            )

        # safe created_at value: try to get attribute, fall back to None or formatted str
        created_dt = getattr(proj, "created_at", None)
        if created_dt is None:
            created_str = None
        else:
            try:
                created_str = created_dt.strftime("%Y-%m-%d")
            except Exception:
                created_str = str(created_dt)

        return templates.TemplateResponse(
            "project_view.html",
            {
                "request": request,
                "project": proj,
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
    # render a blank quote edit/create page
    return templates.TemplateResponse("quote_edit.html", {"request": request, "project_id": project_id, "quote": None, "items": [], "current_year": datetime.utcnow().year})


# --- Create quote (POST) ---
@app.post("/projects/{project_id}/quotes/create")
def create_quote(request: Request, project_id: int, title: str = Form(None), version: int = Form(1), profit_margin: float = Form(0.30), customer_id: int = Form(None), notes: str = Form(None)):
    from app.db import SessionLocal
    from app.models import Quote

    db = SessionLocal()
    try:
        q = Quote(project_id=project_id, title=title, version=version, profit_margin=profit_margin, customer_id=customer_id, notes=notes)
        db.add(q)
        db.commit()
        db.refresh(q)
        # Redirect to edit page so the user can add items
        return RedirectResponse(url=f"/quotes/{q.id}/edit", status_code=303)
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
    from app.models import Quote, QuoteItem

    db = SessionLocal()
    try:
        q = db.query(Quote).filter(Quote.id == quote_id).first()
        if not q:
            return templates.TemplateResponse("quote_edit.html", {"request": request, "quote": None, "items": [], "error": "Quote not found", "current_year": datetime.utcnow().year})
        items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).order_by(QuoteItem.id.asc()).all()
        return templates.TemplateResponse("quote_edit.html", {"request": request, "quote": q, "items": items, "current_year": datetime.utcnow().year})
    finally:
        db.close()


# --- Save quote items (POST JSON) endpoint used by JS from the quote_edit page ---
@app.post("/quotes/{quote_id}/items/save")
def save_quote_items(quote_id: int, payload: dict = Body(...)):
    """
    payload = {
      "items": [ {work_category, work_type, element, supplier, date, item_type, spec, quantity, unit, unit_price, remark}, ... ],
      "profit_margin": 0.25
    }
    """
    from app.db import SessionLocal
    from app.models import Quote, QuoteItem
    db = SessionLocal()
    try:
        q = db.query(Quote).filter(Quote.id == quote_id).first()
        if not q:
            return JSONResponse({"error": "quote not found"}, status_code=404)

        # delete existing items and recreate (simple approach)
        db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).delete()
        db.commit()

        subtotal = 0.0
        for it in payload.get("items", []):
            qty = float(it.get("quantity") or 0)
            unit_price = float(it.get("unit_price") or 0)
            amount = qty * unit_price
            subtotal += amount
            new_item = QuoteItem(
                quote_id=quote_id,
                work_category=it.get("work_category"),
                work_type=it.get("work_type"),
                element=it.get("element"),
                supplier=it.get("supplier"),
                date=it.get("date"),
                item_type=it.get("item_type"),
                spec=it.get("spec"),
                quantity=qty,
                unit=it.get("unit"),
                unit_price=unit_price,
                amount=amount,
                remark=it.get("remark"),
            )
            db.add(new_item)
        q.subtotal = subtotal
        # update margin if provided
        if "profit_margin" in payload:
            q.profit_margin = float(payload["profit_margin"] or q.profit_margin)
        q.total = subtotal * (1.0 + float(q.profit_margin or 0.0))
        db.add(q)
        db.commit()
        db.refresh(q)
        return JSONResponse({"ok": True, "subtotal": q.subtotal, "total": q.total})
    finally:
        db.close()


# --- Delete quote (POST) ---
@app.post("/quotes/{quote_id}/delete")
def delete_quote(quote_id: int):
    from app.db import SessionLocal
    from app.models import Quote
    db = SessionLocal()
    try:
        q = db.query(Quote).filter(Quote.id == quote_id).first()
        if q:
            db.delete(q)
            db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/projects/list", status_code=303)
