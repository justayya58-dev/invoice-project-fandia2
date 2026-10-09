def test_dashboard_summary_has_demo_metrics_and_chart(client):
    response = client.get("/auditpro/dashboard")
    assert response.status_code == 200, response.text
    body = response.json()
    # Metrics are database-derived (not fixed demo constants) so assert shape/sanity, not literal values.
    assert isinstance(body["total_revenue"], (int, float))
    assert isinstance(body["cashflow_net"], (int, float))
    assert body["receivables"] >= 0
    assert 0 <= body["audit_pass_rate"] <= 100
    assert len(body["chart"]) >= 6
    assert "recent_invoices" in body
    assert "period_label" in body and body["period_label"]


def test_dashboard_receivables_matches_sent_or_overdue_invoice_total(client):
    dashboard = client.get("/auditpro/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    invoices = client.get("/auditpro/invoices")
    assert invoices.status_code == 200, invoices.text
    expected = sum(row["total"] for row in invoices.json() if row["status"] in ("sent", "overdue"))
    assert dashboard.json()["receivables"] == expected
