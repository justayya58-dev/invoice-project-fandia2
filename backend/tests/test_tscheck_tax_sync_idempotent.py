"""Criterion: Rekonsiliasi otomatis membuat dokumen pajak dari invoice/transaksi tanpa duplikasi."""

import uuid


def _approve_expense_transaction(client, unique: str) -> dict:
    create_resp = client.post(
        "/auditpro/transactions",
        json={
            "type": "expense",
            "counterparty": f"tscheck-tax-sync-vendor-{unique}",
            "reference_number": f"tscheck-tax-sync-ref-{unique}",
            "category": "Operasional",
            "subtotal": 10000000,
            "tax": 1100000,
            "total": 11100000,
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    transaction = create_resp.json()

    submit_resp = client.post(f"/auditpro/transactions/{transaction['id']}/action", json={"action": "submit", "actor": "tscheck"})
    assert submit_resp.status_code == 200, submit_resp.text
    approve_resp = client.post(f"/auditpro/transactions/{transaction['id']}/action", json={"action": "approve", "actor": "tscheck"})
    assert approve_resp.status_code == 200, approve_resp.text
    return transaction


def test_sync_creates_tax_document_and_is_idempotent(client):
    unique = uuid.uuid4().hex[:8]
    transaction = _approve_expense_transaction(client, unique)

    first_sync = client.post("/auditpro/tax/sync", json={})
    assert first_sync.status_code == 200, first_sync.text
    assert first_sync.json()["created"] >= 1

    docs_resp = client.get("/auditpro/tax/documents?period=2026-10")
    assert docs_resp.status_code == 200, docs_resp.text
    matches = [d for d in docs_resp.json() if d["source_type"] == "transaction" and d["source_id"] == transaction["id"]]
    assert len(matches) == 1, f"expected exactly one tax document for source, got {len(matches)}"
    assert matches[0]["direction"] == "input"
    assert matches[0]["source_reference"] == transaction["reference_number"]

    second_sync = client.post("/auditpro/tax/sync", json={})
    assert second_sync.status_code == 200, second_sync.text

    docs_resp_2 = client.get("/auditpro/tax/documents?period=2026-10")
    assert docs_resp_2.status_code == 200
    matches_after = [d for d in docs_resp_2.json() if d["source_type"] == "transaction" and d["source_id"] == transaction["id"]]
    assert len(matches_after) == 1, "sync must not duplicate source_type+source_id"
