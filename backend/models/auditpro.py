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


class DocumentExtractCreate(BaseModel):
    file_name: str
    file_type: str = "application/pdf"
    file_size: int = 0


class AuditDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str
    file_type: str
    file_size: int
    status: Literal["review", "validated"] = "review"
    confidence: int = 94
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extraction: ExtractionData


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
    total_revenue: float
    revenue_change: float
    cashflow_net: float
    receivables: float
    audit_pass_rate: float
    active_invoices: int
    chart: list[ChartPoint]
    recent_invoices: list[Invoice]