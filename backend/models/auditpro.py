from datetime import datetime, timezone
from typing import Literal
import uuid

from pydantic import BaseModel, Field


class ExtractionData(BaseModel):
    vendor: str
    invoice_number: str
    invoice_date: str
    due_date: str
    subtotal: float
    tax: float
    total: float
    category: str


class AuditDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str
    file_type: str
    file_size: int
    status: Literal["draft", "review", "approved", "rejected"] = "draft"
    confidence: int = 94
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extraction_source: Literal["demo", "gemini-ocr"] = "demo"
    model_name: str = "seed-data"
    transaction_id: str | None = None
    extraction: ExtractionData


class AuditEvent(BaseModel):
    action: Literal["created", "ocr_extracted", "submitted", "approved", "rejected"]
    actor: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: str = ""


class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    transaction_date: str | None = None
    counterparty: str
    reference_number: str
    description: str = ""
    category: str
    subtotal: float = Field(ge=0)
    tax: float = Field(default=0, ge=0)
    total: float = Field(ge=0)


class TransactionActionRequest(BaseModel):
    action: Literal["submit", "approve", "reject"]
    actor: str = "Raka Adinata"
    note: str = ""


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["manual", "ocr", "invoice"]
    document_id: str | None = None
    type: Literal["income", "expense"]
    transaction_date: str
    counterparty: str
    reference_number: str
    description: str = ""
    category: str
    subtotal: float
    tax: float
    total: float
    status: Literal["draft", "review", "approved", "rejected"] = "draft"
    duplicate_suspected: bool = False
    duplicate_of: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit_trail: list[AuditEvent] = Field(default_factory=list)


class InvoiceItem(BaseModel):
    description: str
    quantity: int = 1
    price: float
    total: float


class InvoiceCreate(BaseModel):
    customer: str
    due_date: str
    items: list[InvoiceItem] = Field(default_factory=list)


class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    number: str
    customer: str
    issue_date: str
    due_date: str
    total: float
    status: Literal["paid", "pending", "overdue", "draft"]
    items: list[InvoiceItem] = Field(default_factory=list)


class ChartPoint(BaseModel):
    label: str
    revenue: float
    expenses: float


class DashboardSummary(BaseModel):
    period_label: str
    total_revenue: float
    revenue_change: float
    cashflow_net: float
    receivables: float
    audit_pass_rate: float
    active_invoices: int
    pending_reviews: int
    chart: list[ChartPoint]
    recent_invoices: list[Invoice]


class ReportCategory(BaseModel):
    category: str
    income: float
    expense: float


class ReportSummary(BaseModel):
    period_start: str
    period_end: str
    sales_total: float
    expense_total: float
    net_profit: float
    receivables: float
    tax_collected: float
    tax_paid: float
    approved_count: int
    pending_count: int
    categories: list[ReportCategory]