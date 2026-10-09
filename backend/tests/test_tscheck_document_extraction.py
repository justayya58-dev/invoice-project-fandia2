def test_document_extraction_creates_deterministic_fields(client):
    payload = {'file_name': 'tscheck-upload-unique.pdf', 'file_type': 'application/pdf', 'file_size': 12345}
    response = client.post('/auditpro/documents/extract', json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['file_name'] == payload['file_name']
    assert body['status'] == 'review'
    assert body['confidence'] > 0
    extraction = body['extraction']
    assert extraction['vendor'] == 'Tscheck Upload Unique'
    assert extraction['invoice_number']
    assert extraction['invoice_date']
    assert extraction['due_date']
    assert extraction['total'] == extraction['subtotal'] + extraction['tax']
    assert extraction['category']
