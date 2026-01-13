# app/models.py
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db import Base

from sqlalchemy import Column, Integer, String, Boolean

# ----------------------------------------
# Your original model (KEEP THIS)
# ----------------------------------------
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), nullable=False)
    site = Column(String(255))
    contact = Column(String(255))

    status = Column(String(20), default="active")  # 👈 ADD THIS

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Project id={self.id} client_name={self.client_name!r}>"
# ---------- Customer ----------
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
# ---------- Quote (header) ----------
class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    version = Column(Integer, default=1)
    title = Column(String, nullable=True)
    profit_margin = Column(Float, default=0.30)

    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, default=0.0)

    company_name = Column(
        String,
        default="MK技建株式会社"
    )

    notes = Column(Text, nullable=True)
    status = Column(String, default="draft")

    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ AUTO 支払期限（発行日 + 30日）
    payment_due = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30)
    )

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")


# ---------- Quote Item (each Excel row) ----------
class QuoteItem(Base):
    __tablename__ = "quote_items"
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)

    # Excel columns
    work_category = Column(String, nullable=True)   # 工事区分
    work_type = Column(String, nullable=True)       # 工種
    element = Column(String, nullable=True)         # 要素
    supplier = Column(String, nullable=True)        # 取引業者
    date = Column(String, nullable=True)            # 日付 (string is okay)
    item_type = Column(String, nullable=True)       # 種類
    spec = Column(String, nullable=True)            # 規格

    quantity = Column(Float, default=0.0)           # 数量
    unit = Column(String, nullable=True)            # 単位
    unit_price = Column(Float, default=0.0)         # 単価
    amount = Column(Float, default=0.0)             # 金額

    remark = Column(Text, nullable=True)            # 備考

    # Relationship
    quote = relationship("Quote", back_populates="items")
    



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    

    department = Column(String(50), nullable=True)
    job_title = Column(String(100), nullable=True)