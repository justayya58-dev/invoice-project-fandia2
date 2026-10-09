# AuditPro AI — Living Spec

## Product
AuditPro AI is a dark-first AI Business Document & Financial Management Platform for Indonesian businesses. Development is staged so each phase extends the same document, transaction, invoice, dashboard, and reporting data foundation.

## Current MVP
- Dashboard summary with IDR revenue, cashflow, receivables, audit pass rate, trend chart, and recent invoices.
- Document vault with secure multipart upload, real Gemini 3.8 Flash OCR for PDF/JPG/PNG invoices, confidence score, and validation action.
- Invoice Studio with Modern/Klasik/Minimal templates, company branding and logo, automatic numbering, customer/product masters, live totals and terbilang, PDF/Excel export, and Draft → Terkirim → Lunas/Jatuh Tempo workflow.
- Unified transaction database for income and expenses from OCR or manual input.
- Approval state machine: Draft → Perlu Review → Disetujui/Ditolak, with immutable audit events and duplicate warnings.
- Dashboard and automatic reports calculated from approved transactions, including sales, expenses, net profit, receivables, tax summary, and CSV export.
- Tax Compliance workspace with 0%/11%/12% profiles, automatic source reconciliation, NPWP/faktur/date/DPP/PPN validation, completeness scoring, Draft → Review → Ready → Reported/Needs Correction workflow, tax-period dashboard, CSV/Excel, and e-Faktur preview export.
- Grounded Financial Assistant powered by Gemini 3.8 Flash with SSE token streaming, persisted workspace sessions, quick prompts, business-data context, and audited proposal approval.

## Data model
- `AuditDocument`: id, file metadata, workflow status, linked transaction id, confidence, uploaded timestamp, and extracted vendor/invoice/date/totals/category.
- `Transaction`: source, document link, income/expense type, date, counterparty, reference, category, amounts, workflow status, duplicate marker, and audit trail.
- `Invoice`: automatic number, customer link, template, issue/due dates, subtotal/tax/total, amount words, notes, workflow timestamps/status, and line items linked to products.
- `CompanyProfile`: identity, contact/tax/bank details, accent color, and uploaded logo data.
- `Customer` and `Product`: reusable invoice master data including NPWP, address, SKU, unit, and price.
- `DashboardSummary`: server-anchored reporting period, database-derived metrics, chart points, review count, and recent invoices.
- `ReportSummary`: approved sales, expenses, net profit, receivables, tax inputs/outputs, approval counts, and category totals.
- `TaxDocument`: linked invoice/transaction, input/output direction, counterparty/NPWP, source and tax invoice references, tax period, DPP/rate/PPN, completeness findings, workflow status, and status history.
- `TaxSummary`: tax-period input/output DPP and PPN, net PPN, readiness/issues, workflow counts, and totals by 0%/11%/12% profile.
- `AssistantSession` and `AssistantMessage`: persisted multi-turn workspace conversations.
- `AssistantProposal`: allowlisted pending draft invoice/report action requiring explicit confirmation, with decision and result identifiers.
- `AssistantAuditEvent`: immutable record of messages, proposals, confirmations, and cancellations.
- `AssistantDraftReport`: confirmed report snapshot that never mutates source transactions.

## Key flow
Upload/input transaksi → Gemini extraction or manual draft → review → approve/reject → unified database → invoice recap → dynamic dashboard → report/export CSV.

Invoice flow: choose one of three templates → select customer/product → live quantity/price/tax/terbilang calculation → save with automatic number → export PDF/Excel → mark sent → mark paid; a paid invoice automatically creates an approved income transaction.

Tax flow: sync sent/paid/overdue invoices and approved expenses → complete NPWP, tax invoice number, date, DPP, and rate → automatic PPN validation → review → ready for e-Faktur → reported or returned for correction → export tax-period CSV/Excel/e-Faktur preview.

Assistant flow: choose/create a session → ask about transactions, invoices, receivables, trends, reports, or tax → receive streamed grounded analysis → optionally request a draft invoice/report → review proposal → explicitly confirm or cancel → create only a new draft artifact and record the full audit event.

## Auth
Tidak ada autentikasi pada demo ini. Semua data bersifat lokal/demo.

## Integrations
- Gemini 3.8 Flash melalui Emergent Universal Key membaca isi PDF/gambar invoice dan mengembalikan field terstruktur. File hanya disimpan sementara dan langsung dihapus setelah OCR.
- Financial Assistant uses Gemini 3.8 Flash through the Emergent Universal Key. Only minimized structured business context is sent; raw OCR file binaries are excluded.

## Roadmap
- Tahap 2 (complete): professional invoice generator, three templates, branding/logo, customer/product database, live calculations, terbilang, PDF/Excel, and payment workflow.
- Tahap 3 (complete): 0%/11%/12% profiles, automatic PPN validation, completeness checks, workflow tracking, period reports, CSV/Excel, and e-Faktur preview preparation.
- Tahap 4 (complete): grounded streaming AI over business data, persistent sessions, quick prompts, safeguarded draft proposals, explicit confirmation, and audit trail.
- Tahap 5: smart approvals, enterprise security/access control, external integrations, and predictive analytics.