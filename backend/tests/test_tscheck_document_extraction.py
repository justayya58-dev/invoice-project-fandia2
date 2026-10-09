import os

FIXTURE_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "tscheck_invoice_sample.pdf")


def test_document_extraction_creates_deterministic_fields(client):
    with open(FIXTURE_PDF, "rb") as fh:
        response = client.post(
            "/auditpro/documents/extract",
            files={"file": ("tscheck-upload-unique.pdf", fh, "application/pdf")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["file_name"] == "tscheck-upload-unique.pdf"
    assert body["status"] == "draft"
    assert body["confidence"] > 0
    extraction = body["extraction"]
    assert extraction["vendor"] == "PT Tscheck Mandiri Jaya"
    assert extraction["invoice_number"] == "TSK-INV-90210"
    assert extraction["invoice_date"]
    assert extraction["due_date"]
    assert extraction["total"] == extraction["subtotal"] + extraction["tax"]
    assert extraction["category"]
    # The extracted transaction is linked and raw file is not persisted for re-download.
    assert body["transaction_id"]


def test_invalid_file_signature_is_rejected(client):
    response = client.post(
        "/auditpro/documents/extract",
        files={"file": ("tscheck-bad.txt", b"not a real pdf or image", "text/plain")},
    )
    assert response.status_code == 415, response.text
