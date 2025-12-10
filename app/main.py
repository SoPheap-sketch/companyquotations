# app/main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app import db as _db

app = FastAPI(title="Company Quotation System (MVP)")

# mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------- Startup ----------------
@app.on_event("startup")
def startup_event():
    # initialize database (create tables)
    _db.init_db()


# ---------------- Homepage ----------------
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


# ---------------- Project: Create (POST) ----------------
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

    # Redirect to HTML list after POST (303 recommended)
    return RedirectResponse(url="/projects/list", status_code=303)


# ---------------- Project: JSON API (list) ----------------
@app.get("/projects", response_class=JSONResponse)
def projects_api_list():
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).all()
        data = [
            {"id": p.id, "client_name": p.client_name, "site": p.site, "contact": p.contact}
            for p in projects
        ]
        return JSONResponse(content=data)
    finally:
        db.close()


# ---------------- Project: Create Form (HTML) ----------------
@app.get("/projects/form", response_class=HTMLResponse)
def projects_form(request: Request):
    return templates.TemplateResponse(
        "projects.html",
        {"request": request, "current_year": datetime.utcnow().year},
    )


# ---------------- Project: HTML List Page ----------------
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
        {"request": request, "projects": projects, "current_year": datetime.utcnow().year},
    )


# ---------------- Debug route (dev only) ----------------
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

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return templates.TemplateResponse(
                "project_view.html",
                {
                    "request": request,
                    "project": None,
                    "error": "Project not found",
                    "current_year": datetime.utcnow().year,
                },
            )

        # prepare a safe created_at string for the template
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
