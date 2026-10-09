"""Criterion: Modul Pajak & e-Faktur dashboard period summary exposes PPN profile fields."""

import uuid


def test_tax_summary_has_period_profile_fields(client):
    unique = uuid.uuid4().hex[:8]
    period = "2026-10"

    summary_resp = client.get(f"/auditpro/tax/summary?period={period}")
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()
    for field in ("period", "output_dpp", "output_vat", "input_dpp", "input_vat", "net_vat", "ready_count", "issue_count", "status_counts", "by_rate"):
        assert field in summary, f"missing {field} in {summary}"
    assert summary["period"] == period
    rates_present = {row["rate"] for row in summary["by_rate"]}
    assert rates_present == {0, 11, 12}

    docs_resp = client.get(f"/auditpro/tax/documents?period={period}")
    assert docs_resp.status_code == 200, docs_resp.text
    docs = docs_resp.json()
    assert isinstance(docs, list)
    if docs:
        row = docs[0]
        for field in ("status", "completeness_score", "dpp", "tax_rate", "vat", "tax_period"):
            assert field in row

    profiles_resp = client.get("/auditpro/tax/profiles")
    assert profiles_resp.status_code == 200, profiles_resp.text
    profile_rates = {p["rate"] for p in profiles_resp.json()}
    assert profile_rates == {0, 11, 12}
    assert unique  # keep unique marker referenced for fixture discipline
