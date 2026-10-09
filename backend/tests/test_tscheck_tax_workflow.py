"""Criterion: Workflow pajak Draft/Perlu Perbaikan -> Review -> Siap e-Faktur -> Dilaporkan,
with rejection of mark_ready on incomplete documents and persisted status history.
"""

import uuid

from tests.test_tscheck_tax_validation_completeness import _create_incomplete_tax_document


def test_incomplete_document_rejected_at_mark_ready_then_full_workflow_succeeds(client):
    unique = uuid.uuid4().hex[:8]
    document = _create_incomplete_tax_document(client, unique)
    assert document["status"] == "draft"

    # submit_review is allowed even if incomplete.
    review_resp = client.post(f"/auditpro/tax/documents/{document['id']}/action", json={"action": "submit_review", "actor": "tscheck"})
    assert review_resp.status_code == 200, review_resp.text
    assert review_resp.json()["status"] == "review"

    # mark_ready must be rejected while fields are missing.
    rejected_ready = client.post(f"/auditpro/tax/documents/{document['id']}/action", json={"action": "mark_ready", "actor": "tscheck"})
    assert rejected_ready.status_code == 422, rejected_ready.text

    # Complete the required fields.
    update_resp = client.put(
        f"/auditpro/tax/documents/{document['id']}",
        json={
            "npwp": "01.234.567.8-901.000",
            "tax_invoice_number": f"010.000-26.{unique}",
            "document_date": "2026-10-17",
            "dpp": 5000000,
            "tax_rate": 11,
        },
    )
    assert update_resp.status_code == 200, update_resp.text

    # Editing while in review keeps it in review (not auto needs_correction); re-submit path.
    review_resp_2 = client.post(f"/auditpro/tax/documents/{document['id']}/action", json={"action": "submit_review", "actor": "tscheck"})
    # review -> submit_review has no transition defined; status should already be review from before update.
    current = client.get("/auditpro/tax/documents?period=2026-10").json()
    current_doc = next(d for d in current if d["id"] == document["id"])
    assert current_doc["status"] in {"review", "needs_correction"}
    if current_doc["status"] == "needs_correction":
        client.post(f"/auditpro/tax/documents/{document['id']}/action", json={"action": "submit_review", "actor": "tscheck"})

    ready_resp = client.post(f"/auditpro/tax/documents/{document['id']}/action", json={"action": "mark_ready", "actor": "tscheck"})
    assert ready_resp.status_code == 200, ready_resp.text
    assert ready_resp.json()["status"] == "ready"

    reported_resp = client.post(f"/auditpro/tax/documents/{document['id']}/action", json={"action": "mark_reported", "actor": "tscheck"})
    assert reported_resp.status_code == 200, reported_resp.text
    final = reported_resp.json()
    assert final["status"] == "reported"

    statuses = [event["status"] for event in final["status_history"]]
    assert "draft" in statuses and "review" in statuses and "ready" in statuses and "reported" in statuses
    assert unique
