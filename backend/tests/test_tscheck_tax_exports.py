"""Criterion: Laporan masa pajak dapat diexport ke CSV, Excel, dan preview e-Faktur."""


def test_csv_export_returns_valid_attachment(client):
    resp = client.get("/auditpro/tax/export.csv?period=2026-10")
    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")
    body = resp.text
    assert "Arah" in body.splitlines()[0]


def test_xlsx_export_returns_valid_zip_based_office_file(client):
    resp = client.get("/auditpro/tax/export.xlsx?period=2026-10")
    assert resp.status_code == 200, resp.text
    assert "spreadsheetml" in resp.headers.get("content-type", "")
    assert resp.content[:2] == b"PK", "xlsx is a zip container and must start with PK signature"


def test_efaktur_preview_only_contains_ready_or_reported_documents(client):
    resp = client.get("/auditpro/tax/efaktur-preview.csv?period=2026-10")
    assert resp.status_code == 200, resp.text
    assert "attachment" in resp.headers.get("content-disposition", "")
    rows = resp.text.strip().splitlines()
    assert rows[0].startswith("FK,")

    docs_resp = client.get("/auditpro/tax/documents?period=2026-10")
    ready_or_reported_refs = {
        d["tax_invoice_number"] for d in docs_resp.json() if d["status"] in {"ready", "reported"} and d["tax_invoice_number"]
    }
    data_rows = rows[1:]
    for row in data_rows:
        fields = row.split(",")
        invoice_number = fields[3]
        if invoice_number:
            assert invoice_number in ready_or_reported_refs, f"{invoice_number} should only come from ready/reported docs"
