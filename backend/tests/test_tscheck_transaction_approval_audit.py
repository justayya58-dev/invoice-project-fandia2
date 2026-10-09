def create_tscheck_transaction(client, reference_suffix):
    payload = {
        "type": "expense",
        "transaction_date": "2026-05-01",
        "counterparty": "tscheck-approval-vendor",
        "reference_number": f"TSK-APPROVAL-{reference_suffix}",
        "description": "Pengeluaran uji approval",
        "category": "Operasional",
        "subtotal": 1000000,
        "tax": 110000,
        "total": 1110000,
    }
    response = client.post("/auditpro/transactions", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_approve_workflow_moves_draft_to_approved_with_audit_trail(client):
    transaction = create_tscheck_transaction(client, "approve-1")
    tid = transaction["id"]
    assert transaction["status"] == "draft"

    submit = client.post(f"/auditpro/transactions/{tid}/action", json={"action": "submit", "actor": "Tester"})
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "review"

    approve = client.post(f"/auditpro/transactions/{tid}/action", json={"action": "approve", "actor": "Tester"})
    assert approve.status_code == 200, approve.text
    body = approve.json()
    assert body["status"] == "approved"
    actions = [event["action"] for event in body["audit_trail"]]
    assert "submitted" in actions
    assert "approved" in actions


def test_reject_workflow_moves_review_to_rejected_with_note(client):
    transaction = create_tscheck_transaction(client, "reject-1")
    tid = transaction["id"]
    client.post(f"/auditpro/transactions/{tid}/action", json={"action": "submit"})

    reject = client.post(f"/auditpro/transactions/{tid}/action", json={"action": "reject", "note": "Bukti tidak lengkap"})
    assert reject.status_code == 200, reject.text
    body = reject.json()
    assert body["status"] == "rejected"
    rejected_event = next(e for e in body["audit_trail"] if e["action"] == "rejected")
    assert rejected_event["note"] == "Bukti tidak lengkap"


def test_invalid_transition_is_rejected(client):
    transaction = create_tscheck_transaction(client, "invalid-1")
    tid = transaction["id"]
    # draft cannot jump straight to approve
    response = client.post(f"/auditpro/transactions/{tid}/action", json={"action": "approve"})
    assert response.status_code == 409
