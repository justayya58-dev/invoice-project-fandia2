def test_created_document_can_be_validated(client):
    created = client.post('/auditpro/documents/extract', json={
        'file_name': 'tscheck-validation-unique.jpg',
        'file_type': 'image/jpeg',
        'file_size': 23456,
    })
    assert created.status_code == 200, created.text
    document_id = created.json()['id']
    response = client.post(f'/auditpro/documents/{document_id}/validate', json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['id'] == document_id
    assert body['status'] == 'validated'


def test_unknown_document_validation_is_rejected(client):
    response = client.post('/auditpro/documents/tscheck-missing-document/validate', json={})
    assert response.status_code == 404
