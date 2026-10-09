import os

FIXTURE_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "tscheck_invoice_sample.pdf")


def test_resubmitting_same_invoice_reference_and_total_is_flagged_duplicate(client):
    with open(FIXTURE_PDF, "rb") as fh:
        first = client.post(
            "/auditpro/documents/extract",
            files={"file": ("tscheck-dup-first.pdf", fh, "application/pdf")},
        )
    assert first.status_code == 200, first.text
    first_transaction_id = first.json()["transaction_id"]

    with open(FIXTURE_PDF, "rb") as fh:
        second = client.post(
            "/auditpro/documents/extract",
            files={"file": ("tscheck-dup-second.pdf", fh, "application/pdf")},
        )
    assert second.status_code == 200, second.text
    second_transaction_id = second.json()["transaction_id"]

    transactions = client.get("/auditpro/transactions")
    assert transactions.status_code == 200, transactions.text
    rows = {row["id"]: row for row in transactions.json()}

    # The fixture reference+total may already exist from earlier runs; what matters is that the
    # second upload of an identical reference+total is detected as a duplicate of an earlier one.
    assert rows[second_transaction_id]["duplicate_suspected"] is True
    assert rows[second_transaction_id]["duplicate_of"] is not None
    assert rows[second_transaction_id]["duplicate_of"] != second_transaction_id
