import os

FIXTURE_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "tscheck_invoice_sample.pdf")


def test_created_document_can_be_validated(client):
    with open(FIXTURE_PDF, "rb") as fh:
        created = client.post(
            "/auditpro/documents/extract",
            files={"file": ("tscheck-validation-unique.pdf", fh, "application/pdf")},
        )
    assert created.status_code == 200, created.text
    body = created.json()
    document_id = body["id"]
    transaction_id = body["transaction_id"]

    # Workflow is draft -> review (submit) -> approved; validation == full approval of the linked transaction.
    submit = client.post(f"/auditpro/transactions/{transaction_id}/action", json={"action": "submit"})
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "review"

    approve = client.post(f"/auditpro/transactions/{transaction_id}/action", json={"action": "approve"})
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "approved"

    documents = client.get("/auditpro/documents")
    assert documents.status_code == 200, documents.text
    matched = next((d for d in documents.json() if d["id"] == document_id), None)
    assert matched is not None
    assert matched["status"] == "approved"


def test_unknown_transaction_action_is_rejected(client):
    response = client.post("/auditpro/transactions/tscheck-missing-transaction/action", json={"action": "approve"})
    assert response.status_code == 404
