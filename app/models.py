
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

    status = Column(String(20), default="active")  

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

    # AUTO 支払期限（発行日 + 30日）
    payment_due = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30)
    )

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_name = Column(String(100), nullable=True)
    approved_by_role = Column(String(50), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    approved_by = relationship("User", lazy="joined")
    # Relationships
    project = relationship("Project", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")

    invoice = relationship ("Invoice", back_populates="quote", uselist=False)

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

    role = Column(String(20), default="staff")     # admin / ceo / staff
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)

    is_admin = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    force_password_change = Column(Boolean, default=False)
#Create Approval Log Model
class QuoteApprovalLog(Base):
    __tablename__ = "quote_approval_logs"
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)  # approved / rejected
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationships
    quote = relationship("Quote", backref="approval_logs")
    # user = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)  

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)

    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", lazy="joined")

class WorkInstruction(Base):
    __tablename__ = "work_instructions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(String(20), default="pending")  
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User",foreign_keys=[assigned_to])

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)
    work_instruction_id = Column(
        Integer,
        ForeignKey("work_instructions.id"),
        nullable=True
    )

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    quote = relationship("Quote")
    work_instruction = relationship(
        "WorkInstruction",
        backref="attachments"
    )
    uploader = relationship("User")
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    work_instruction_id = Column(Integer, ForeignKey("work_instructions.id"), nullable=True)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", lazy="joined")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index= True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date =Column(DateTime, nullable=True)

    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, default=0.0)

    payment_status = Column(String(20), default="unpaid")  # unpaid / paid / overdue
    payment_date = Column(DateTime,nullable=True)
    notes = Column(String(255),nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    quote = relationship("Quote", back_populates="invoice")

#-----------------Receipt-----------------
class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)

    receipt_number = Column(String(50), unique=True, nullable=False)

    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String(100), nullable=True)

    amount_received = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", lazy="joined")