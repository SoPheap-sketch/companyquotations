# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import db as _db
from app.routes.pages import router as pages_router
from app.routes.api import router as api_router
from app.pdf_utils import render_pdf_from_html

app = FastAPI(title="Company Quotation System")

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup_event():
    _db.init_db()

# Routers
app.include_router(pages_router)
app.include_router(api_router)
