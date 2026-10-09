"""Criterion: Validasi kelengkapan memeriksa NPWP, nomor faktur, tanggal, DPP, dan perhitungan PPN."""

import uuid


def _create_incomplete_tax_document(client, unique: str) -> dict:
    tx_resp = client.post(
        "/auditpro/transactions",
        json={
            "type": "expense",
            "counterparty": f"tscheck-tax-complete-vendor-{unique}",
            "reference_number": f"tscheck-tax-complete-ref-{unique}",
            "category": "Operasional",
            "subtotal": 5000000,
            "tax": 550000,
            "total": 5550000,
        },
    )
    assert tx_resp.status_code == 200, tx_resp.text
    transaction = tx_resp.json()
    client.post(f"/auditpro/transactions/{transaction['id']}/action", json={"action": "submit", "actor": "tscheck"})
    client.post(f"/auditpro/transactions/{transaction['id']}/action", json={"action": "approve", "actor": "tscheck"})
    client.post("/auditpro/tax/sync", json={})

    docs_resp = client.get("/auditpro/tax/documents?period=2026-10")
    matches = [d for d in docs_resp.json() if d["source_type"] == "transaction" and d["source_id"] == transaction["id"]]
    assert len(matches) == 1
    return matches[0]


def test_completeness_score_reaches_100_after_filling_required_fields(client):
    unique = uuid.uuid4().hex[:8]
    document = _create_incomplete_tax_document(client, unique)
    # Freshly synced expense transaction document has no NPWP / tax invoice number -> incomplete.
    assert document["completeness_score"] < 100
    assert "NPWP" in document["missing_fields"]

    update_resp = client.put(
        f"/auditpro/tax/documents/{document['id']}",
        json={
            "npwp": "01.234.567.8-901.000",
            "tax_invoice_number": f"010.000-26.{unique}",
            "document_date": "2026-10-15",
            "dpp": 5000000,
            "tax_rate": 11,
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["completeness_score"] == 100, updated
    assert updated["missing_fields"] == []
    assert updated["vat"] == round(5000000 * 11 / 100, 2)
