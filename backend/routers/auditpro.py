from fastapi import APIRouter, File, HTTPException, UploadFile
import csv
from datetime import date, datetime, timezone
import io
import uuid

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument

from lib.dates import today_iso
from lib.db import db
from models.auditpro import (
    AuditDocument,
    AuditEvent,
    DashboardSummary,
    ExtractionData,
    Invoice,
    InvoiceCreate,
    InvoiceItem,
    ReportCategory,
    ReportSummary,
    Transaction,
    TransactionActionRequest,
    TransactionCreate,
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
            status="approved",
            transaction_id="TRX-DEMO-003",
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
            transaction_id="TRX-DEMO-002",
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
    await db.audit_documents.update_many({"status": "validated"}, {"$set": {"status": "approved"}})
    await db.audit_documents.update_one({"id": "DOC-2401"}, {"$set": {"transaction_id": "TRX-DEMO-003"}})
    await db.audit_documents.update_one({"id": "DOC-2402"}, {"$set": {"transaction_id": "TRX-DEMO-002"}})


async def ensure_demo_invoices() -> None:
    if await db.audit_invoices.count_documents({}) == 0:
        await db.audit_invoices.insert_many([item.model_dump() for item in demo_invoices()])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def month_date(month_offset: int, day: int = 8) -> str:
    today = date.fromisoformat(today_iso())
    month_index = today.year * 12 + today.month - 1 + month_offset
    year, month_zero = divmod(month_index, 12)
    return date(year, month_zero + 1, min(day, 28)).isoformat()


def event(action: str, note: str, actor: str = "System") -> AuditEvent:
    return AuditEvent(action=action, actor=actor, note=note)


def demo_transactions() -> list[Transaction]:
    rows = [
        ("TRX-DEMO-001", "income", 0, "PT Arunika Jaya", "INV-2025-001", "Penjualan jasa konsultasi", "Penjualan", 24750000, 2722500, 27472500, "approved"),
        ("TRX-DEMO-002", "expense", 0, "Sahabat Logistik", "SL-8831", "Biaya logistik", "Operasional", 4250000, 467500, 4717500, "review"),
        ("TRX-DEMO-003", "expense", -1, "PT Nusantara Teknologi", "INV-NT-0248", "Langganan perangkat lunak", "Software & Teknologi", 18500000, 2035000, 20535000, "approved"),
        ("TRX-DEMO-004", "income", -1, "CV Kreasi Digital", "INV-2025-002", "Implementasi sistem", "Penjualan", 36000000, 3960000, 39960000, "approved"),
        ("TRX-DEMO-005", "expense", -2, "PT Ruang Kerja", "OFF-889", "Sewa kantor", "Fasilitas", 12000000, 1320000, 13320000, "approved"),
        ("TRX-DEMO-006", "income", -2, "PT Satu Visi", "INV-2024-088", "Retainer bulanan", "Penjualan", 31500000, 3465000, 34965000, "approved"),
        ("TRX-DEMO-007", "income", -3, "Studio Langit", "INV-2024-071", "Produksi kampanye", "Penjualan", 42000000, 4620000, 46620000, "approved"),
        ("TRX-DEMO-008", "expense", -3, "Cloud Infrastruktur", "CLD-772", "Infrastruktur cloud", "Teknologi", 9500000, 1045000, 10545000, "approved"),
        ("TRX-DEMO-009", "income", -4, "PT Karya Utama", "INV-2024-050", "Audit operasional", "Penjualan", 28500000, 3135000, 31635000, "approved"),
        ("TRX-DEMO-010", "income", -5, "Nusa Retail", "INV-2024-031", "Integrasi data", "Penjualan", 22000000, 2420000, 24420000, "approved"),
    ]
    transactions: list[Transaction] = []
    for identifier, kind, offset, counterparty, reference, description, category, subtotal, tax, total, status in rows:
        action = "approved" if status == "approved" else "submitted"
        transactions.append(Transaction(
            id=identifier,
            source="ocr" if identifier in {"TRX-DEMO-002", "TRX-DEMO-003"} else "manual",
            document_id="DOC-2402" if identifier == "TRX-DEMO-002" else "DOC-2401" if identifier == "TRX-DEMO-003" else None,
            type=kind,
            transaction_date=month_date(offset),
            counterparty=counterparty,
            reference_number=reference,
            description=description,
            category=category,
            subtotal=subtotal,
            tax=tax,
            total=total,
            status=status,
            audit_trail=[event("created", "Data awal workspace"), event(action, "Status awal demo", "Raka Adinata")],
        ))
    return transactions


async def ensure_demo_transactions() -> None:
    if await db.audit_transactions.count_documents({}) == 0:
        await db.audit_transactions.insert_many([item.model_dump() for item in demo_transactions()])


async def duplicate_match(reference_number: str, total: float) -> Transaction | None:
    if not reference_number or reference_number.lower() == "tidak terdeteksi":
        return None
    match = await db.audit_transactions.find_one({"reference_number": reference_number, "total": total})
    return Transaction(**match) if match else None


async def report_summary(period_start: str, period_end: str) -> ReportSummary:
    await ensure_demo_transactions()
    await ensure_demo_invoices()
    docs = await db.audit_transactions.find({"transaction_date": {"$gte": period_start, "$lte": period_end}}).to_list(1000)
    transactions = [Transaction(**doc) for doc in docs]
    approved = [item for item in transactions if item.status == "approved"]
    sales = sum(item.total for item in approved if item.type == "income")
    expenses = sum(item.total for item in approved if item.type == "expense")
    categories: dict[str, dict[str, float]] = {}
    for item in approved:
        bucket = categories.setdefault(item.category, {"income": 0.0, "expense": 0.0})
        bucket[item.type] += item.total
    receivables = await db.audit_invoices.aggregate([
        {"$match": {"status": {"$in": ["pending", "overdue"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}},
    ]).to_list(1)
    return ReportSummary(
        period_start=period_start,
        period_end=period_end,
        sales_total=sales,
        expense_total=expenses,
        net_profit=sales - expenses,
        receivables=receivables[0]["total"] if receivables else 0,
        tax_collected=sum(item.tax for item in approved if item.type == "income"),
        tax_paid=sum(item.tax for item in approved if item.type == "expense"),
        approved_count=len(approved),
        pending_count=sum(item.status in {"draft", "review"} for item in transactions),
        categories=[ReportCategory(category=key, **value) for key, value in sorted(categories.items())],
    )


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard() -> DashboardSummary:
    await ensure_demo_invoices()
    await ensure_demo_transactions()
    invoice_docs = await db.audit_invoices.find().sort("issue_date", -1).to_list(4)
    invoices = [Invoice(**invoice) for invoice in invoice_docs]
    today = date.fromisoformat(today_iso())
    current_start = today.replace(day=1).isoformat()
    current_end = today.isoformat()
    current = await report_summary(current_start, current_end)
    previous_end = date.fromisoformat(month_date(-1, 28))
    previous_start = previous_end.replace(day=1).isoformat()
    previous = await report_summary(previous_start, previous_end.isoformat())
    change = ((current.sales_total - previous.sales_total) / previous.sales_total * 100) if previous.sales_total else 0
    status_counts = await db.audit_transactions.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]).to_list(10)
    counts = {item["_id"]: item["count"] for item in status_counts}
    decided = counts.get("approved", 0) + counts.get("rejected", 0)
    chart: list[dict] = []
    for offset in range(-5, 1):
        point = date.fromisoformat(month_date(offset))
        start = point.replace(day=1).isoformat()
        end = date(point.year, point.month, 28).isoformat()
        summary = await report_summary(start, end)
        chart.append({"label": point.strftime("%b"), "revenue": round(summary.sales_total / 1_000_000, 1), "expenses": round(summary.expense_total / 1_000_000, 1)})
    return DashboardSummary(
        period_label=f"01 — {today.strftime('%d %b %Y').upper()}",
        total_revenue=current.sales_total,
        revenue_change=round(change, 1),
        cashflow_net=current.net_profit,
        receivables=current.receivables,
        audit_pass_rate=round(counts.get("approved", 0) / decided * 100, 1) if decided else 0,
        active_invoices=sum(invoice.status in {"pending", "overdue"} for invoice in invoices),
        pending_reviews=counts.get("review", 0),
        chart=chart,
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
    duplicate = await duplicate_match(extraction.invoice_number, extraction.total)
    transaction = Transaction(
        source="ocr",
        document_id=document.id,
        type="expense",
        transaction_date=extraction.invoice_date or today_iso(),
        counterparty=extraction.vendor,
        reference_number=extraction.invoice_number,
        description=f"Hasil OCR dari {document.file_name}",
        category=extraction.category,
        subtotal=extraction.subtotal,
        tax=extraction.tax,
        total=extraction.total,
        duplicate_suspected=duplicate is not None,
        duplicate_of=duplicate.id if duplicate else None,
        audit_trail=[event("ocr_extracted", f"Diekstrak dengan {OCR_MODEL}")],
    )
    document.transaction_id = transaction.id
    await db.audit_transactions.insert_one(transaction.model_dump())
    await db.audit_documents.insert_one(document.model_dump())
    return document


@router.post("/documents/{document_id}/validate", response_model=AuditDocument)
async def validate_document(document_id: str) -> AuditDocument:
    await ensure_demo_documents()
    document = await db.audit_documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    parsed = AuditDocument(**document)
    transaction_id = parsed.transaction_id
    if transaction_id:
        await db.audit_transactions.update_one(
            {"id": transaction_id},
            {"$set": {"status": "approved", "updated_at": now_iso()}, "$push": {"audit_trail": event("approved", "Validasi kompatibilitas", "Raka Adinata").model_dump()}},
        )
    updated = await db.audit_documents.find_one_and_update(
        {"id": document_id}, {"$set": {"status": "approved"}}, return_document=ReturnDocument.AFTER
    )
    return AuditDocument(**updated)


@router.get("/transactions", response_model=list[Transaction])
async def get_transactions() -> list[Transaction]:
    await ensure_demo_transactions()
    docs = await db.audit_transactions.find().sort("created_at", -1).to_list(500)
    return [Transaction(**doc) for doc in docs]


@router.post("/transactions", response_model=Transaction)
async def create_transaction(input: TransactionCreate) -> Transaction:
    await ensure_demo_transactions()
    if abs(input.total - (input.subtotal + input.tax)) > 0.01:
        raise HTTPException(status_code=422, detail="Total harus sama dengan subtotal ditambah pajak")
    if input.transaction_date:
        try:
            date.fromisoformat(input.transaction_date)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Format tanggal transaksi harus YYYY-MM-DD") from exc
    duplicate = await duplicate_match(input.reference_number, input.total)
    transaction = Transaction(
        source="manual",
        type=input.type,
        transaction_date=input.transaction_date or today_iso(),
        counterparty=input.counterparty,
        reference_number=input.reference_number,
        description=input.description,
        category=input.category,
        subtotal=input.subtotal,
        tax=input.tax,
        total=input.total,
        duplicate_suspected=duplicate is not None,
        duplicate_of=duplicate.id if duplicate else None,
        audit_trail=[event("created", "Transaksi dibuat manual", "Raka Adinata")],
    )
    await db.audit_transactions.insert_one(transaction.model_dump())
    return transaction


@router.post("/transactions/{transaction_id}/action", response_model=Transaction)
async def transition_transaction(transaction_id: str, input: TransactionActionRequest) -> Transaction:
    await ensure_demo_transactions()
    current_doc = await db.audit_transactions.find_one({"id": transaction_id})
    if not current_doc:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    current = Transaction(**current_doc)
    transitions = {("draft", "submit"): "review", ("review", "approve"): "approved", ("review", "reject"): "rejected"}
    target = transitions.get((current.status, input.action))
    if not target:
        raise HTTPException(status_code=409, detail=f"Aksi {input.action} tidak valid untuk status {current.status}")
    action_name = {"submit": "submitted", "approve": "approved", "reject": "rejected"}[input.action]
    audit = event(action_name, input.note or f"Status diubah ke {target}", input.actor)
    updated = await db.audit_transactions.find_one_and_update(
        {"id": transaction_id},
        {"$set": {"status": target, "updated_at": now_iso()}, "$push": {"audit_trail": audit.model_dump()}},
        return_document=ReturnDocument.AFTER,
    )
    if current.document_id:
        await db.audit_documents.update_one({"id": current.document_id}, {"$set": {"status": target}})
    return Transaction(**updated)


def report_period(start: str | None, end: str | None) -> tuple[str, str]:
    today = date.fromisoformat(today_iso())
    period_start = start or today.replace(day=1).isoformat()
    period_end = end or today.isoformat()
    try:
        date.fromisoformat(period_start)
        date.fromisoformat(period_end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Format tanggal laporan harus YYYY-MM-DD") from exc
    if period_start > period_end:
        raise HTTPException(status_code=422, detail="Tanggal awal tidak boleh melewati tanggal akhir")
    return period_start, period_end


@router.get("/reports/summary", response_model=ReportSummary)
async def get_report_summary(start: str | None = Query(default=None), end: str | None = Query(default=None)) -> ReportSummary:
    period_start, period_end = report_period(start, end)
    return await report_summary(period_start, period_end)


@router.get("/reports/export.csv")
async def export_report_csv(start: str | None = Query(default=None), end: str | None = Query(default=None)):
    period_start, period_end = report_period(start, end)
    await ensure_demo_transactions()
    docs = await db.audit_transactions.find({"transaction_date": {"$gte": period_start, "$lte": period_end}}).sort("transaction_date", -1).to_list(1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tanggal", "Tipe", "Referensi", "Pihak", "Kategori", "Subtotal", "Pajak", "Total", "Status", "Sumber"])
    for doc in docs:
        item = Transaction(**doc)
        writer.writerow([item.transaction_date, item.type, item.reference_number, item.counterparty, item.category, item.subtotal, item.tax, item.total, item.status, item.source])
    filename = f"auditpro-report-{period_start}-{period_end}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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