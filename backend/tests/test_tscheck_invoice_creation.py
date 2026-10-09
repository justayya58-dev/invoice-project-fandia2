def test_invoice_database_and_draft_creation(client):
    listed = client.get("/auditpro/invoices")
    assert listed.status_code == 200, listed.text
    assert isinstance(listed.json(), list)

    payload = {
        "customer": "tscheck-customer-unique",
        "due_date": "2030-04-30",
        "items": [{"description": "Jasa konsultasi tscheck", "unit": "jasa", "quantity": 2, "price": 2500000, "total": 5000000}],
        "tax_rate": 11,
    }
    response = client.post("/auditpro/invoices", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["customer"] == payload["customer"]
    assert body["due_date"] == payload["due_date"]
    assert body["status"] == "draft"
    assert body["subtotal"] == 5000000
    assert body["tax"] == 550000
    assert body["total"] == 5550000
    assert body["items"]
    assert body["number"]

    # auto-numbering is unique per created invoice
    second = client.post("/auditpro/invoices", json=payload)
    assert second.status_code == 200, second.text
    assert second.json()["number"] != body["number"]

    refetched = client.get("/auditpro/invoices")
    assert any(row["id"] == body["id"] for row in refetched.json())


def test_invoice_rejects_due_date_before_today(client):
    response = client.post("/auditpro/invoices", json={"customer": "tscheck-invalid-date", "due_date": "2000-01-01"})
    assert response.status_code == 422
