from app.db import SessionLocal
from app.models import Project, Quote, QuoteItem, User
from app.auth.utils import hash_password
from datetime import datetime
import random

db = SessionLocal()

# -------------------------------
# USERS
# -------------------------------
def create_users():
    users = [
        User(
            username="admin3",
            password="admin123",
            is_admin=True,
        ),
        User(
            username="sopheap1",
            password="123456",
            is_admin=False,
        ),
        User(
            username="architect1",
            password="123456",
            is_admin=False,
        ),
        User(
            username="designer1",
            password="123456",
            is_admin=False,
        ),
        User(
            username="manager1",
            password="123456",
            is_admin=False,
        ),
    ]

    for u in users:
        if not db.query(User).filter(User.username == u.username).first():
            db.add(u)

    db.commit()
    print("✅ Users created")


# -------------------------------
# PROJECTS + QUOTES + ITEMS
# -------------------------------
def create_projects_and_quotes():
    for i in range(1, 8):
        project = Project(
            client_name=f"Test Client {i}",
            site=f"Phnom Penh Site {i}",
            contact=f"01234567{i}",
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Create 1–3 quotes per project
        for q in range(random.randint(1, 3)):
            quote = Quote(
                project_id=project.id,
                title=f"Estimate v{q+1}",
                status=random.choice(["draft", "pending", "approved"]),
                profit_margin=0.3,
            )
            db.add(quote)
            db.commit()
            db.refresh(quote)

            subtotal = 0

            # Create items
            for item_index in range(random.randint(3, 6)):
                qty = random.randint(1, 10)
                price = random.randint(50, 500)

                item = QuoteItem(
                    quote_id=quote.id,
                    element=f"Work Item {item_index+1}",
                    quantity=qty,
                    unit_price=price,
                    amount=qty * price,
                )
                subtotal += item.amount
                db.add(item)

            quote.subtotal = subtotal
            quote.tax = subtotal * 0.1
            quote.total = quote.subtotal + quote.tax

            db.commit()

    print("✅ Projects, quotes, and items created")


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    create_users()
    create_projects_and_quotes()
    db.close()
    print("🎉 Test data seeding complete")
