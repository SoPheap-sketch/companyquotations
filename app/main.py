from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import db as _db
from app.routes.pages import router as pages_router
from app.routes.api import router as api_router
from app.routes.quotes import router as quotes_router
from app.routes.auth import router as auth_router
from app.routes import admin, attachments, work_instructions
from app.routes.notifications import router as notifications_router
from app.routes import invoices

from app.db import SessionLocal
from app.models import User
from app.routes.auth_utils import get_password_hash 
from fastapi.responses import RedirectResponse

app = FastAPI(title="Company Quotation System")

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-this"
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# @app.on_event("startup")
# def startup_event():
#     _db.init_db()
@app.get("/")
def read_root():
      return RedirectResponse("/dashboard")
    
@app.on_event("startup")
def startup_event():
    _db.init_db()


# Routers
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(quotes_router)
app.include_router(auth_router)
app.include_router(admin.router)
app.include_router(work_instructions.router)
app.include_router(attachments.router)
app.include_router(notifications_router)
app.include_router(invoices.router)
