# app/main.py
from fastapi import FastAPI, Request, Form
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
