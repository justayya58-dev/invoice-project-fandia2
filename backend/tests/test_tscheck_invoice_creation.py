def test_invoice_database_and_draft_creation(client):
    listed = client.get('/auditpro/invoices')
    assert listed.status_code == 200, listed.text
    assert any(row['number'].startswith('INV-2025-') for row in listed.json())

    payload = {'customer': 'tscheck-customer-unique', 'due_date': '2030-04-30'}
    response = client.post('/auditpro/invoices', json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['customer'] == payload['customer']
    assert body['due_date'] == payload['due_date']
    assert body['status'] == 'draft'
    assert body['total'] == 5000000
    assert body['items']
