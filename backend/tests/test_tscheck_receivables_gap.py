def test_dashboard_and_report_receivables_derive_from_sent_or_overdue_invoices(client):
    invoices = client.get("/auditpro/invoices")
    assert invoices.status_code == 200, invoices.text
    rows = invoices.json()
    expected_receivables = sum(row["total"] for row in rows if row["status"] in ("sent", "overdue"))

    dashboard = client.get("/auditpro/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["receivables"] == expected_receivables

    report = client.get("/auditpro/reports/summary")
    assert report.status_code == 200, report.text
    assert report.json()["receivables"] == expected_receivables


def test_no_aging_bucket_or_partial_payment_fields_on_invoice(client):
    """Documents the current gap: invoices only carry a single status/paid_at, no
    aging bucket, partial-payment ledger, or reminder/follow-up fields exist yet."""
    invoices = client.get("/auditpro/invoices")
    assert invoices.status_code == 200, invoices.text
    rows = invoices.json()
    assert rows, "expected at least one invoice to inspect the schema"
    sample = rows[0]
    for absent_field in ("aging_bucket", "amount_paid", "reminder_sent_at", "payments"):
        assert absent_field not in sample
