# AuditPro AI — Living Spec

## Product
AuditPro AI is a dark-first finance operations workspace for Indonesian businesses. It manages invoices and business documents with local/demo AI extraction, validation, reporting, receivables, and a financial assistant shell.

## Current MVP
- Dashboard summary with IDR revenue, cashflow, receivables, audit pass rate, trend chart, and recent invoices.
- Document vault with secure multipart upload, real Gemini 3.8 Flash OCR for PDF/JPG/PNG invoices, confidence score, and validation action.
- Invoice database with realistic Indonesian demo data and draft invoice creation.
- Financial Assistant panel with local/demo responses.

## Data model
- `AuditDocument`: id, file metadata, review/validated status, confidence, uploaded timestamp, extracted vendor/invoice/date/totals/category.
- `Invoice`: id, number, customer, issue/due dates, total, status, and line items.
- `DashboardSummary`: north-star metrics, chart points, and recent invoices.

## Key flow
Open dashboard → pilih Dokumen → pilih file PDF/JPG/PNG maksimal 10 MB → jalankan Gemini OCR → review field hasil → validasi dokumen.

## Auth
Tidak ada autentikasi pada demo ini. Semua data bersifat lokal/demo.

## Integrations
- Gemini 3.8 Flash melalui Emergent Universal Key membaca isi PDF/gambar invoice dan mengembalikan field terstruktur. File hanya disimpan sementara dan langsung dihapus setelah OCR.
- Financial Assistant masih MOCKED secara deterministik untuk preview.