"""Criterion: Profil tarif 0%, 11%, 12% dapat dipilih dan PPN dihitung otomatis (VAT = DPP x rate)."""

import uuid

from tests.test_tscheck_tax_validation_completeness import _create_incomplete_tax_document


def test_changing_rate_recomputes_vat_for_each_profile(client):
    unique = uuid.uuid4().hex[:8]
    document = _create_incomplete_tax_document(client, unique)

    for rate, dpp in ((0, 2000000), (11, 3000000), (12, 4000000)):
        update_resp = client.put(
            f"/auditpro/tax/documents/{document['id']}",
            json={
                "npwp": "01.234.567.8-901.000",
                "tax_invoice_number": f"010.000-26.{unique}-{rate}",
                "document_date": "2026-10-16",
                "dpp": dpp,
                "tax_rate": rate,
            },
        )
        assert update_resp.status_code == 200, update_resp.text
        updated = update_resp.json()
        assert updated["tax_rate"] == rate
        assert updated["vat"] == round(dpp * rate / 100, 2), updated
