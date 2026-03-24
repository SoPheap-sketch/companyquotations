# app/routes/pages.py

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone
import json

from app import db
from app.db import SessionLocal

from app.pdf_utils import render_pdf_from_html
from app.services.auth import login_required

from app.models import Project, Quote, QuoteItem, User, QuoteApprovalLog, Receipt
from app.utils.audit import write_audit_log
from app.models import AuditLog   
from app.services.auth import admin_only
from app.models import WorkInstruction
from typing import Optional
from fastapi import Query
from app.models import User
from sqlalchemy import func
from sqlalchemy.sql import extract
from app.services.notifications import get_unread_notification_count

from app.models import Notification
import pytz
import csv
import io
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =====================================================
# DASHBOARD
# =====================================================
@router.get("/", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def dashboard(request: Request):
    db = SessionLocal()
    try:
        role = request.session.get("role")
        can_view_money= role in ["admin", "manager", "ceo", ]

        total_projects = db.query(Project).count()
        pending_estimates = db.query(Quote).filter(Quote.status == "pending").count()
        approved_quotes = db.query(Quote).filter(Quote.status == "approved").count()

        total_approved_amount = (
            db.query(func.coalesce(func.sum(Receipt.amount_received), 0))
            .scalar()
        ) or 0
        if not can_view_money:
            total_approved_amount = 0
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
                "notification_count": get_unread_notification_count(request),
                "total_projects": total_projects,
                "pending_estimates": pending_estimates,
                "approved_quotes": approved_quotes,
                "total_approved_amount": total_approved_amount,
                "can_view_money": can_view_money,
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
    request: Request,  
    client_name: str = Form(...),
    site: str = Form(None),
    contact: str = Form(None),
):
    db = SessionLocal()
    try:
        project = Project(
            client_name=client_name,
            site=site,
            contact=contact
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        write_audit_log(
            request=request,
            action="CREATE_PROJECT",
            description=f"Created project '{project.client_name}' (ID {project.id})",
            target_user_id=request.session.get("user_id"),
        )

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
        instructions = (
            db.query(WorkInstruction)
            .filter(WorkInstruction.project_id == project_id)
            .order_by(WorkInstruction.created_at.desc())
            .all()
        )
        assignable_users = (
            db.query(User)
            .filter(
                User.is_active == True,
                User.role.in_(["staff", "manager", "admin"])
            )
            .order_by(User.role, User.username)
            .all()
        )
        return templates.TemplateResponse(
            "project_view.html",
            {
                "request": request,
                "project": project,
                "quotes": quotes,
                "instructions": instructions,
                "assignable_users": assignable_users,
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
    request: Request,
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

        # 1. Update project fields
        project.client_name = client_name
        project.site = site
        project.contact = contact
        write_audit_log(
            request=request,
            action="UPDATE_PROJECT",
            description=f"Updated project '{client_name}' (ID {project_id})",
            target_user_id=request.session.get("user_id"),
        )
        
        # 3. Commit everything at once
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Error updating project: {e}")
        raise HTTPException(500, "Internal Server Error")
    finally:
        db.close()
    return RedirectResponse(f"/projects/{project_id}", status_code=303)

@router.post("/projects/{project_id}/delete", dependencies=[Depends(login_required)])
def delete_project(request: Request, project_id: int):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id:
        raise HTTPException(401)

    if role not in ["admin", "manager", "ceo"]:
        raise HTTPException(403)

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(404)

        # BLOCK if approved quotes exist
        approved_quotes = (
            db.query(Quote)
            .filter(
                Quote.project_id == project_id,
                Quote.status == "approved"
            )
            .count()
        )

        if approved_quotes > 0:
            request.session["flash_error"] = (
                "❌ Cannot delete project. Approved quotes exist."
            )
            return RedirectResponse(
                f"/projects/{project_id}",
                status_code=303
            )

        project_name = project.client_name

        db.delete(project)
        db.commit()

        request.session["flash_success"] = (
            f"✅ Project '{project_name}' deleted successfully."
        )

        write_audit_log(
            request=request,
            action="DELETE_PROJECT",
            description=f"Deleted project '{project_name}' (ID {project_id})",
            target_user_id=user_id,
        )

        return RedirectResponse("/projects/list", status_code=303)

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
def delete_quote(request: Request, quote_id: int):
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if quote:
            project_id = quote.project_id

            db.delete(quote)
            db.commit()

            write_audit_log(
                request=request,
                action="DELETE_QUOTE",
                description=f"Deleted quote #{quote_id} (Project #{project_id})",
                target_user_id=request.session.get("user_id"),
            )

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

        # Handle payment due date
        if quote.payment_due is None:
            quote.payment_due = quote.created_at + timedelta(days=30)
            db.commit()
            db.refresh(quote)

        # --- CALCULATE SELLING PRICE (Cost + Profit) ---
        # This ensures 'subtotal' and 'total' passed to HTML include the margin
        calc_subtotal = 0
        margin = quote.profit_margin or 0
        
        for item in quote.items:
            unit_cost = item.unit_price or 0
            qty = item.quantity or 0
            # Calculate selling price per unit (integer)
            selling_price_unit = int(unit_cost * (1 + margin))
            calc_subtotal += (selling_price_unit * qty)
        
        calc_tax = int(calc_subtotal * 0.10)
        calc_total = calc_subtotal + calc_tax
        # -----------------------------------------------

        # Render the template with the CALCULATED values
        html_content = templates.get_template("quote_pdf.html").render({
            "request": request,
            "quote": quote,
            "items": quote.items,
            "subtotal": calc_subtotal,  # Sent to HTML as {{ subtotal }}
            "tax": calc_tax,            # Sent to HTML as {{ tax }}
            "total": calc_total,        # Sent to HTML as {{ total }}
            "payment_due": quote.payment_due.strftime("%Y/%m/%d"),
        })

        pdf = render_pdf_from_html(html_content)

        write_audit_log(
            request=request,
            action="GENERATE_QUOTE_PDF",
            description=f"Generated PDF for quote #{quote.id}",
            target_user_id=request.session.get("user_id"),
        )
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=file.pdf"
            }
        )
        # return StreamingResponse(
        #     pdf,
        #     media_type="application/pdf",
        #     headers={"Content-Disposition": f"inline; filename=quote_{quote.id}.pdf"}
        # )
    finally:
        db.close()
CAMBODIA_TZ = pytz.timezone("Asia/Phnom_Penh")

@router.get(
    "/admin/audit-logs",
    response_class=HTMLResponse,
    dependencies=[Depends(admin_only)],
)
def audit_logs(
    request: Request,
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    db = SessionLocal()

    try:
        # =========================
        # SAFE USER_ID CONVERSION
        # =========================
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                user_id_int = None
        # =========================
        # BASE QUERY
        # =========================
        query = (
            db.query(
                AuditLog.id,
                AuditLog.action,
                AuditLog.description,
                AuditLog.ip_address,
                AuditLog.created_at,
                User.username,
            )
            .outerjoin(User, User.id == AuditLog.user_id)
        )
        # =========================
        # APPLY FILTERS
        # =========================
        if user_id_int is not None:
            query = query.filter(AuditLog.user_id == user_id_int)

        if action:
            query = query.filter(AuditLog.action == action)

        if from_date:
            query = query.filter(
                AuditLog.created_at >= datetime.fromisoformat(from_date)
            )

        if to_date:
            query = query.filter(
                AuditLog.created_at
                < datetime.fromisoformat(to_date) + timedelta(days=1)
            )
        # EXECUTE QUERY

        logs = query.order_by(AuditLog.created_at.desc()).all()
        # =========================
        # FORMAT FOR TEMPLATE (UTC ➜ CAMBODIA TIME)
        # =========================
        formatted_logs = []
        for row in logs:
            local_time = (
                row.created_at
                .replace(tzinfo=pytz.utc)
                .astimezone(CAMBODIA_TZ)
            )

            formatted_logs.append({
                "id": row.id,
                "action": row.action,
                "description": row.description,
                "ip_address": row.ip_address,
                "username": row.username,
                "created_at": local_time,  #  Cambodia time
            })
        # =========================
        # FILTER DROPDOWNS DATA
        # =========================
        users = db.query(User).order_by(User.username).all()

        actions = (
            db.query(AuditLog.action)
            .distinct()
            .order_by(AuditLog.action)
            .all()
        )
        actions = [a[0] for a in actions]

        # =========================
        # RENDER TEMPLATE
        # =========================
        return templates.TemplateResponse(
            "admin_audit_logs.html",
            {
                "request": request,
                "logs": formatted_logs,
                "users": users,
                "actions": actions,
                "filters": {
                    "user_id": user_id_int,
                    "action": action,
                    "from_date": from_date,
                    "to_date": to_date,
                },
            },
        )

    finally:
        db.close()
       
@router.get(
    "/admin/audit-logs/export",
    dependencies=[Depends(admin_only)],
)
def export_audit_logs_csv(
    request: Request,
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    db = SessionLocal()

    try:
        # ---- SAFE USER ID ----
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                pass

        # ---- BASE QUERY ----
        query = (
            db.query(
                AuditLog.created_at,
                AuditLog.action,
                AuditLog.description,
                AuditLog.ip_address,
                User.username,
            )
            .outerjoin(User, User.id == AuditLog.user_id)
        )

        # ---- FILTERS ----
        if user_id_int:
            query = query.filter(AuditLog.user_id == user_id_int)

        if action:
            query = query.filter(AuditLog.action == action)

        if from_date:
            query = query.filter(
                AuditLog.created_at >= datetime.fromisoformat(from_date)
            )

        if to_date:
            query = query.filter(
                AuditLog.created_at
                < datetime.fromisoformat(to_date) + timedelta(days=1)
            )

        logs = query.order_by(AuditLog.created_at.desc()).all()

        # ---- CREATE CSV IN MEMORY ----
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Time",
            "User",
            "Action",
            "Description",
            "IP Address",
        ])

        # Rows
        for log in logs:
            writer.writerow([
                log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                log.username or "System",
                log.action,
                log.description,
                log.ip_address or "",
            ])

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=audit_logs.csv"
            },
        )

    finally:
        db.close()
@router.get("/reports", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def reports(request: Request):
    db = SessionLocal()
    try:
        role = request.session.get("role")
        can_view_money = role in ["admin", "manager", "ceo"]
        monthly_sales = []
        
        if can_view_money:
            rows = (
                db.query(
                    extract("month", Quote.created_at).label("month"),
                    func.coalesce(func.sum(Quote.total), 0).label("total")
                )
                .filter(Quote.status == "approved")
                .group_by("month")
                .order_by("month")
                .all()
            )
            

            # Convert to simple arrays for Chart.js
            monthly_sales = [
                {
                    "month": int(row.month),
                    "total": float(row.total)
                }
                for row in rows
            ]
        workflow_rows = (
            db.query(
                Quote.status,
                func.count(Quote.id)
            )
            .group_by(Quote.status)
            .all()
        )

        workflow_data = {
            status: count
            for status, count in workflow_rows
        }
        return templates.TemplateResponse(
            "reports.html",
            {
                "request": request,
                "role": role,
                "can_view_money": can_view_money,
                "monthly_sales": monthly_sales,
                "workflow_data": workflow_data,
                "current_year": datetime.utcnow().year,
            },
        )
    finally:
        db.close()


@router.get("/notifications")
def view_notifications(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()
    try:
        notifications = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

        return templates.TemplateResponse(
            "notifications.html",
            {
                "request": request,
                "notifications": notifications,
            }
        )
    finally:
        db.close()

@router.post("/notifications/mark-read")
def mark_notifications_read(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401)

    db = SessionLocal()
    try:
        db.query(Notification)\
          .filter(Notification.user_id == user_id)\
          .update({"is_read": True})
        db.commit()
        return {"ok": True}
    finally:
        db.close()
