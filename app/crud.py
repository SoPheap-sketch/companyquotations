# app/crud.py
from sqlalchemy.orm import Session
from datetime import timedelta

from app.models import Project, Quote, QuoteItem


# ==================================================
# PROJECT CRUD
# ==================================================

def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session):
    return db.query(Project).order_by(Project.id.desc()).all()


def create_project(db: Session, client_name: str, site: str = None, contact: str = None):
    project = Project(
        client_name=client_name,
        site=site,
        contact=contact,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: int, client_name: str, site: str, contact: str):
    project = get_project(db, project_id)
    if not project:
        return None

    project.client_name = client_name
    project.site = site
    project.contact = contact
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int):
    project = get_project(db, project_id)
    if project:
        db.delete(project)
        db.commit()
    return project


# ==================================================
# DASHBOARD / COUNTS
# ==================================================

def count_projects(db: Session):
    return db.query(Project).count()


def count_pending_estimates(db: Session):
    return (
        db.query(Quote)
        .filter(Quote.status.in_(["draft", "pending"]))
        .count()
    )


def count_approved_quotes(db: Session):
    return (
        db.query(Quote)
        .filter(Quote.status == "approved")
        .count()
    )


def recent_projects(db: Session, limit: int = 5):
    return (
        db.query(Project)
        .order_by(Project.id.desc())
        .limit(limit)
        .all()
    )


def recent_quotes(db: Session, limit: int = 5):
    return (
        db.query(Quote)
        .order_by(Quote.id.desc())
        .limit(limit)
        .all()
    )


# ==================================================
# QUOTE CRUD
# ==================================================

def get_quote(db: Session, quote_id: int):
    return db.query(Quote).filter(Quote.id == quote_id).first()


def get_project_quotes(db: Session, project_id: int):
    return (
        db.query(Quote)
        .filter(Quote.project_id == project_id)
        .order_by(Quote.version.asc(), Quote.id.desc())
        .all()
    )


def create_draft_quote(db: Session, project_id: int):
    quote = Quote(
        project_id=project_id,
        status="draft",
        profit_margin=0.30,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def delete_quote(db: Session, quote_id: int):
    quote = get_quote(db, quote_id)
    if quote:
        db.delete(quote)
        db.commit()
    return quote


# ==================================================
# QUOTE ITEMS
# ==================================================

def get_quote_items(db: Session, quote_id: int):
    return (
        db.query(QuoteItem)
        .filter(QuoteItem.quote_id == quote_id)
        .order_by(QuoteItem.id.asc())
        .all()
    )


def save_quote_items(db: Session, quote: Quote, items: list):
    # reset items
    db.query(QuoteItem).filter(
        QuoteItem.quote_id == quote.id
    ).delete()

    total_cost = 0

    for item in items:
        qty = float(item.get("quantity", 0))
        price = float(item.get("unit_price", 0))
        amount = qty * price
        total_cost += amount

        db.add(QuoteItem(
            quote_id=quote.id,
            work_category=item.get("work_category"),
            work_type=item.get("work_type"),
            element=item.get("element"),
            supplier=item.get("supplier"),
            quantity=qty,
            unit=item.get("unit"),
            unit_price=price,
            amount=amount,
            spec=item.get("spec"),
            remark=item.get("remark"),
        ))

    quote.subtotal = int(total_cost)
    quote.selling_price = int(total_cost * (1 + quote.profit_margin))
    quote.tax = int(quote.selling_price * 0.10)
    quote.total = quote.selling_price + quote.tax

    if not quote.payment_due:
        quote.payment_due = quote.created_at + timedelta(days=30)

    db.commit()
    db.refresh(quote)
    return quote


# ==================================================
# QUOTE STATUS
# ==================================================

def submit_quote(db: Session, quote_id: int):
    quote = get_quote(db, quote_id)
    if not quote or quote.status != "draft":
        return None

    quote.status = "pending"
    db.commit()
    return quote


def approve_quote(db: Session, quote_id: int):
    quote = get_quote(db, quote_id)
    if not quote or quote.status != "pending":
        return None

    quote.status = "approved"
    db.commit()
    return quote
