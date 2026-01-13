from app.db import SessionLocal
from app.models import Quote, QuoteItem
from datetime import timedelta

def create_draft_quote(project_id: int):
    db = SessionLocal()
    try:
        quote = Quote(
            project_id=project_id,
            title="Draft Quote",
            status="draft",
            profit_margin=0.30,

    
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote
    finally:
        db.close()
def get_quote_or_400(db, quote_id: int):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return None
    return quote