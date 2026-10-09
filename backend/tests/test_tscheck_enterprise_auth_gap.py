def test_no_authentication_is_enforced_on_sensitive_endpoints(client):
    """Documents the current single-user/no-login posture (Tahap 5 enterprise auth not implemented).

    Every workspace endpoint accepts anonymous requests; there is no 401/403 gate, no role header,
    and no per-user scoping. This is a GAP against the enterprise acceptance criterion, not a
    regression, since no auth/roles have ever been declared complete in memory/SPEC.md.
    """
    for method, path, kwargs in [
        ("get", "/auditpro/dashboard", {}),
        ("get", "/auditpro/transactions", {}),
        ("post", "/auditpro/transactions", {"json": {
            "type": "expense", "counterparty": "tscheck-noauth", "reference_number": "TSK-NOAUTH-1",
            "category": "Operasional", "subtotal": 1000, "tax": 0, "total": 1000,
        }}),
        ("get", "/auditpro/tax/summary", {}),
    ]:
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code < 401, f"{method.upper()} {path} unexpectedly required auth: {response.status_code}"


def test_no_role_or_permission_field_exists_on_transaction_schema(client):
    response = client.get("/auditpro/transactions")
    assert response.status_code == 200, response.text
    rows = response.json()
    assert rows, "expected at least one transaction to inspect the schema"
    sample = rows[0]
    for absent_field in ("approver_role", "required_role", "permissions", "approval_threshold"):
        assert absent_field not in sample
