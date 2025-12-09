from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db as _db

app = FastAPI(title="Company Quotation System (MVP)")

# mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup_event():
    # initialize database (create tables)
    _db.init_db()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Quotation Dashboard"})


# ---------- Project endpoints (add below index) ----------
from fastapi import Form
from fastapi.responses import JSONResponse

@app.post("/projects/create")
def create_project(client_name: str = Form(...), site: str = Form(None), contact: str = Form(None)):
    # local imports to avoid circular imports at module load
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        proj = Project(client_name=client_name, site=site, contact=contact)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return {"id": proj.id, "client_name": proj.client_name, "site": proj.site, "contact": proj.contact}
    finally:
        db.close()

@app.get("/projects", response_class=JSONResponse)
def list_projects():
    from app.db import SessionLocal
    from app.models import Project

    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).all()
        data = [{"id": p.id, "client_name": p.client_name, "site": p.site, "contact": p.contact} for p in projects]
        return JSONResponse(content=data)
    finally:
        db.close()

@app.get("/projects/form", response_class=HTMLResponse)
def projects_form(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})
