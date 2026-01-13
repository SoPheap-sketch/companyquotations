# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import db as _db
from app.routes.pages import router as pages_router
from app.routes.api import router as api_router
from app.pdf_utils import render_pdf_from_html
from app.routes.quotes import router as quotes_router

from starlette.middleware.sessions import SessionMiddleware
from app.routes.auth import router as auth_router

app = FastAPI(title="Company Quotation System")
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-this"
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup_event():
    _db.init_db()

# Routers
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(quotes_router)
app.include_router(auth_router)
