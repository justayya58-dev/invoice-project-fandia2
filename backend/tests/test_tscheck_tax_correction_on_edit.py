"""Criterion: Dokumen siap/dilaporkan yang diedit kembali masuk status Perlu Perbaikan."""

import uuid

from tests.test_tscheck_tax_validation_completeness import _create_incomplete_tax_document


def _complete_and_advance_to_reported(client, document_id: str, unique: str) -> dict:
    client.put(
        f"/auditpro/tax/documents/{document_id}",
        json={
            "npwp": "01.234.567.8-901.000",
            "tax_invoice_number": f"010.000-26.{unique}",
            "document_date": "2026-10-18",
            "dpp": 5000000,
            "tax_rate": 11,
        },
    )
    client.post(f"/auditpro/tax/documents/{document_id}/action", json={"action": "submit_review", "actor": "tscheck"})
    ready = client.post(f"/auditpro/tax/documents/{document_id}/action", json={"action": "mark_ready", "actor": "tscheck"})
    assert ready.status_code == 200, ready.text
    reported = client.post(f"/auditpro/tax/documents/{document_id}/action", json={"action": "mark_reported", "actor": "tscheck"})
    assert reported.status_code == 200, reported.text
    return reported.json()


def test_editing_reported_document_moves_to_needs_correction(client):
    unique = uuid.uuid4().hex[:8]
    document = _create_incomplete_tax_document(client, unique)
    reported = _complete_and_advance_to_reported(client, document["id"], unique)
    assert reported["status"] == "reported"

    edit_resp = client.put(
        f"/auditpro/tax/documents/{document['id']}",
        json={
            "npwp": "01.234.567.8-901.000",
            "tax_invoice_number": f"010.000-26.{unique}-edited",
            "document_date": "2026-10-19",
            "dpp": 6000000,
            "tax_rate": 11,
        },
    )
    assert edit_resp.status_code == 200, edit_resp.text
    edited = edit_resp.json()
    assert edited["status"] == "needs_correction", edited
    history_statuses = [event["status"] for event in edited["status_history"]]
    assert history_statuses[-1] == "needs_correction"
