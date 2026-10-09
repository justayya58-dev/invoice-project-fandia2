import uuid

SUFFIX = uuid.uuid4().hex[:8]


def create_invoice(client, due_date="2030-01-01"):
    payload = {
        "customer": f"tscheck-payment-customer-{SUFFIX}",
        "due_date": due_date,
        "items": [{"description": "Jasa tscheck", "unit": "jasa", "quantity": 1, "price": 1200000, "total": 1200000}],
        "tax_rate": 11,
    }
    response = client.post("/auditpro/invoices", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_draft_to_sent_to_paid_creates_income_transaction(client):
    invoice = create_invoice(client)
    invoice_id = invoice["id"]

    send = client.post(f"/auditpro/invoices/{invoice_id}/action", json={"action": "send"})
    assert send.status_code == 200, send.text
    assert send.json()["status"] == "sent"

    paid = client.post(f"/auditpro/invoices/{invoice_id}/action", json={"action": "mark_paid"})
    assert paid.status_code == 200, paid.text
    paid_body = paid.json()
    assert paid_body["status"] == "paid"
    assert paid_body["paid_at"]

    transactions = client.get("/auditpro/transactions")
    assert transactions.status_code == 200, transactions.text
    matches = [t for t in transactions.json() if t["source"] == "invoice" and t["reference_number"] == invoice["number"]]
    assert len(matches) == 1
    income_tx = matches[0]
    assert income_tx["type"] == "income"
    assert income_tx["status"] == "approved"
    assert income_tx["total"] == invoice["total"]


def test_invalid_invoice_transition_is_rejected(client):
    invoice = create_invoice(client, due_date="2030-02-01")
    # cannot mark_paid directly from draft
    response = client.post(f"/auditpro/invoices/{invoice['id']}/action", json={"action": "mark_paid"})
    assert response.status_code == 409
