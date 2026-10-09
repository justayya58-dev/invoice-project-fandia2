from fastapi import APIRouter, File, HTTPException, UploadFile
from pymongo import ReturnDocument

from lib.dates import today_iso
from lib.db import db
from models.auditpro import (
    AuditDocument,
    DashboardSummary,
    ExtractionData,
    Invoice,
    InvoiceCreate,
    InvoiceItem,
)
from services.ocr import OCR_MODEL, OcrExtractionError, extract_invoice

router = APIRouter(prefix="/auditpro", tags=["auditpro"])

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
FILE_SIGNATURES = {
    "application/pdf": (b"%PDF-", ".pdf"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
}


def demo_documents() -> list[AuditDocument]:
    return [
        AuditDocument(
            id="DOC-2401",
            file_name="invoice-pt-nusantara.pdf",
            file_type="application/pdf",
            file_size=245760,
            status="validated",
            confidence=98,
            uploaded_at="2025-02-28T09:14:00+00:00",
            extraction=ExtractionData(
                vendor="PT Nusantara Teknologi",
                invoice_number="INV-NT-0248",
                invoice_date="2025-02-28",
                due_date="2025-03-30",
                subtotal=18500000,
                tax=2035000,
                total=20535000,
                category="Software & Teknologi",
            ),
        ),
        AuditDocument(
            id="DOC-2402",
            file_name="receipt-logistik-maret.jpg",
            file_type="image/jpeg",
            file_size=184320,
            status="review",
            confidence=87,
            uploaded_at="2025-02-27T15:42:00+00:00",
            extraction=ExtractionData(
                vendor="Sahabat Logistik",
                invoice_number="SL-8831",
                invoice_date="2025-02-27",
                due_date="2025-03-15",
                subtotal=4250000,
                tax=467500,
                total=4717500,
                category="Operasional",
            ),
        ),
    ]


def demo_invoices() -> list[Invoice]:
    return [
        Invoice(id="INV-101", number="INV-2025-001", customer="PT Arunika Jaya", issue_date="2025-02-10", due_date="2025-03-12", total=24750000, status="paid", items=[]),
        Invoice(id="INV-102", number="INV-2025-002", customer="CV Kreasi Digital", issue_date="2025-02-18", due_date="2025-03-20", total=13860000, status="pending", items=[]),
        Invoice(id="INV-103", number="INV-2025-003", customer="PT Satu Visi", issue_date="2025-01-22", due_date="2025-02-22", total=8250000, status="overdue", items=[]),
        Invoice(id="INV-104", number="INV-2025-004", customer="Studio Langit", issue_date="2025-02-26", due_date="2025-03-28", total=5940000, status="pending", items=[]),
    ]


async def ensure_demo_documents() -> None:
    if await db.audit_documents.count_documents({}) == 0:
        await db.audit_documents.insert_many([item.model_dump() for item in demo_documents()])


async def ensure_demo_invoices() -> None:
    if await db.audit_invoices.count_documents({}) == 0:
        await db.audit_invoices.insert_many([item.model_dump() for item in demo_invoices()])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard() -> DashboardSummary:
    await ensure_demo_invoices()
    invoice_docs = await db.audit_invoices.find().sort("issue_date", -1).to_list(4)
    invoices = [Invoice(**invoice) for invoice in invoice_docs]
    return DashboardSummary(
        total_revenue=284650000,
        revenue_change=12.8,
        cashflow_net=186420000,
        receivables=74830000,
        audit_pass_rate=96.4,
        active_invoices=12,
        chart=[
            {"label": "Sep", "revenue": 180, "expenses": 92},
            {"label": "Okt", "revenue": 235, "expenses": 118},
            {"label": "Nov", "revenue": 210, "expenses": 104},
            {"label": "Des", "revenue": 286, "expenses": 142},
            {"label": "Jan", "revenue": 264, "expenses": 127},
            {"label": "Feb", "revenue": 318, "expenses": 151},
        ],
        recent_invoices=invoices,
    )


@router.get("/documents", response_model=list[AuditDocument])
async def get_documents() -> list[AuditDocument]:
    await ensure_demo_documents()
    documents = await db.audit_documents.find().sort("uploaded_at", -1).to_list(100)
    return [AuditDocument(**document) for document in documents]


@router.post("/documents/extract", response_model=AuditDocument)
async def extract_document(file: UploadFile = File(...)) -> AuditDocument:
    file_bytes = await file.read(MAX_DOCUMENT_BYTES + 1)
    await file.close()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="File kosong tidak dapat diproses")
    if len(file_bytes) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran file maksimal 10 MB")

    detected_type: str | None = None
    suffix = ""
    for mime_type, (signature, extension) in FILE_SIGNATURES.items():
        if file_bytes.startswith(signature):
            detected_type = mime_type
            suffix = extension
            break
    if not detected_type:
        raise HTTPException(status_code=415, detail="Format file harus PDF, JPG, atau PNG yang valid")

    try:
        extraction, confidence = await extract_invoice(file_bytes, detected_type, suffix)
    except OcrExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    document = AuditDocument(
        file_name=file.filename or f"dokumen{suffix}",
        file_type=detected_type,
        file_size=len(file_bytes),
        confidence=confidence,
        extraction_source="gemini-ocr",
        model_name=OCR_MODEL,
        extraction=extraction,
    )
    await db.audit_documents.insert_one(document.model_dump())
    return document


@router.post("/documents/{document_id}/validate", response_model=AuditDocument)
async def validate_document(document_id: str) -> AuditDocument:
    await ensure_demo_documents()
    document = await db.audit_documents.find_one_and_update(
        {"id": document_id}, {"$set": {"status": "validated"}}, return_document=ReturnDocument.AFTER
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    return AuditDocument(**document)


@router.get("/invoices", response_model=list[Invoice])
async def get_invoices() -> list[Invoice]:
    await ensure_demo_invoices()
    invoices = await db.audit_invoices.find().sort("issue_date", -1).to_list(100)
    return [Invoice(**invoice) for invoice in invoices]


@router.post("/invoices", response_model=Invoice)
async def create_invoice(input: InvoiceCreate) -> Invoice:
    items = input.items or [InvoiceItem(description="Layanan konsultasi", quantity=1, price=5000000, total=5000000)]
    invoice = Invoice(
        number=f"INV-{today_iso().replace('-', '')}-{str(uuid.uuid4())[:4].upper()}",
        customer=input.customer,
        issue_date=today_iso(),
        due_date=input.due_date,
        total=sum(item.total for item in items),
        status="draft",
        items=items,
    )
    await db.audit_invoices.insert_one(invoice.model_dump())
    return invoice