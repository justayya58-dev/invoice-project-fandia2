import uuid

SUFFIX = uuid.uuid4().hex[:8]


def test_customer_create_and_list(client):
    name = f"tscheck-customer-{SUFFIX}"
    payload = {"name": name, "email": "tscheck@example.com", "phone": "081200000000", "address": "Jl. Tscheck No. 1", "tax_id": "01.234.567.8-901.000"}
    created = client.post("/auditpro/customers", json=payload)
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["name"] == name
    assert body["id"]

    listed = client.get("/auditpro/customers")
    assert listed.status_code == 200, listed.text
    assert any(row["id"] == body["id"] for row in listed.json())


def test_product_create_and_list(client):
    sku = f"TSCHECK-{SUFFIX}"
    payload = {"name": f"tscheck-product-{SUFFIX}", "sku": sku, "unit": "pcs", "price": 75000, "description": "Produk uji"}
    created = client.post("/auditpro/products", json=payload)
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["sku"] == sku
    assert body["price"] == 75000

    listed = client.get("/auditpro/products")
    assert listed.status_code == 200, listed.text
    assert any(row["id"] == body["id"] for row in listed.json())


def test_created_customer_and_product_can_be_used_as_invoice_line(client):
    customer = client.post("/auditpro/customers", json={"name": f"tscheck-invoice-customer-{SUFFIX}", "email": "", "phone": "", "address": "", "tax_id": ""}).json()
    product = client.post("/auditpro/products", json={"name": f"tscheck-invoice-product-{SUFFIX}", "sku": f"SKU-{SUFFIX}", "unit": "pcs", "price": 250000, "description": ""}).json()

    invoice_payload = {
        "customer": customer["name"],
        "customer_id": customer["id"],
        "due_date": "2030-01-01",
        "items": [{"product_id": product["id"], "description": product["name"], "unit": "pcs", "quantity": 3, "price": 250000, "total": 750000}],
        "tax_rate": 11,
    }
    invoice = client.post("/auditpro/invoices", json=invoice_payload)
    assert invoice.status_code == 200, invoice.text
    body = invoice.json()
    assert body["customer_id"] == customer["id"]
    assert body["subtotal"] == 750000
    assert round(body["tax"]) == 82500
    assert round(body["total"]) == 832500
