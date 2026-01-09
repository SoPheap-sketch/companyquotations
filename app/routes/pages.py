# app/routes/pages.py

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json

# PDF (REAL PDF)


from app.db import SessionLocal
from app.models import Project, Quote, QuoteItem
from fastapi.responses import StreamingResponse, Response
from datetime import timedelta
from app.pdf_utils import render_pdf_from_html



router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =====================================================
# DASHBOARD
# =====================================================
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    db = SessionLocal()
    try:
        total_projects = db.query(Project).count()

        pending_estimates = db.query(Quote).filter(
            Quote.status == "pending"
        ).count()

        approved_quotes = db.query(Quote).filter(
            Quote.status == "approved"
        ).count()

        # ✅ RECENT ACTIVITY
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
@router.get("/projects/list", response_class=HTMLResponse)
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


@router.get("/projects/form", response_class=HTMLResponse)
def project_form(request: Request):
    return templates.TemplateResponse(
        "projects.html",
        {"request": request, "current_year": datetime.utcnow().year},
    )


@router.post("/projects/create")
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


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def view_project(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(404)

        quotes = db.query(Quote).filter(
            Quote.project_id == project_id
        ).order_by(Quote.id.desc()).all()

        created_at = project.created_at.strftime("%Y-%m-%d")

        return templates.TemplateResponse(
            "project_view.html",
            {
                "request": request,
                "project": project,
                "quotes": quotes,
                "created_at": created_at,  
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
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


@router.post("/projects/{project_id}/edit")
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


@router.post("/projects/{project_id}/delete")
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


# ✅ MUST START AT COLUMN 0
@router.get("/projects/{project_id}/quotes/new", response_class=HTMLResponse)
def new_quote_form(request: Request, project_id: int):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

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
@router.get("/quotes/{quote_id}", response_class=HTMLResponse)
def view_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        items = db.query(QuoteItem).filter(
            QuoteItem.quote_id == quote_id
        ).all()

        return templates.TemplateResponse(
            "quote_view.html",
            {
                "request": request,
                "quote": quote,
                "items": items,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()

# @router.get("/quotes/list", response_class=HTMLResponse)
# def quotes_list(request: Request):
#     db = SessionLocal()
#     try:
#         quotes = (
#             db.query(Quote)
#             .order_by(Quote.created_at.desc())
#             .all()
#         )

#         return templates.TemplateResponse(
#             "quotes_list.html",
#             {
#                 "request": request,
#                 "quotes": quotes,
#                 "current_year": datetime.utcnow().year,
#             },
#         )
#     finally:
#         db.close()


@router.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
def edit_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404)

        if quote.status == "approved":
            raise HTTPException(
                status_code=403,
                detail="Approved quotes cannot be edited"
            )

        items = db.query(QuoteItem).filter(
            QuoteItem.quote_id == quote_id
        ).all()

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
                    }
                    for i in items
                ]),
                "project_id": quote.project_id,
            },
        )
    finally:
        db.close()



@router.post("/quotes/{quote_id}/delete")
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
@router.get("/quotes/{quote_id}/pdf")
def quote_pdf(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        # Auto payment due (発行日 + 30日)
        if quote.payment_due is None:
            quote.payment_due = quote.created_at + timedelta(days=30)
            db.commit()
            db.refresh(quote)

        pdf_items = []
        selling_subtotal = 0

        for it in quote.items:
            selling_unit_price = int(it.unit_price * (1 + quote.profit_margin))
            selling_amount = selling_unit_price * it.quantity
            selling_subtotal += selling_amount

            pdf_items.append({
                "element": it.element,
                "quantity": it.quantity,
                "unit": it.unit,
                "unit_price": selling_unit_price,
                "amount": selling_amount,
                "remark": it.remark,
            })

        tax = int(selling_subtotal * 0.10)
        total = selling_subtotal + tax

        html = templates.get_template("quote_pdf.html").render({
            "request": request,
            "quote": quote,
            "items": pdf_items,
            "subtotal": selling_subtotal,
            "tax": tax,
            "total": total,
            "payment_due": quote.payment_due.strftime("%Y/%m/%d"),
        })

        pdf = render_pdf_from_html(html)

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=quote_{quote.id}.pdf"
            },
        )
    finally:
        db.close()
@router.head("/quotes/{quote_id}/pdf")
def quote_pdf_head():
    return Response(status_code=200)

@router.post("/quotes/{quote_id}/approve")
def approve_quote(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()

        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        if quote.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Only pending quotes can be approved"
            )

        quote.status = "approved"
        db.commit()

    finally:
        db.close()

    return RedirectResponse(
        url=f"/quotes/{quote_id}",
        status_code=303
    )

@router.post("/quotes/{quote_id}/submit")
def submit_quote_for_approval(quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()

        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        if quote.status != "draft":
            raise HTTPException(
                status_code=400,
                detail="Only draft quotes can be submitted"
            )

        quote.status = "pending"
        db.commit()
    finally:
        db.close()

    return RedirectResponse(
        url=f"/quotes/{quote_id}",
        status_code=303
    )
