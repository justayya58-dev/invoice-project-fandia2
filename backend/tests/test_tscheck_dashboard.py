def test_dashboard_summary_has_demo_metrics_and_chart(client):
    response = client.get('/auditpro/dashboard')
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['total_revenue'] == 284650000
    assert body['cashflow_net'] == 186420000
    assert body['receivables'] == 74830000
    assert body['audit_pass_rate'] == 96.4
    assert len(body['chart']) >= 6
    assert 'recent_invoices' in body
