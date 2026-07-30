from . import models


def _post_init_hook(env):
    """Advance the DATEV customer sequence past the highest existing identifier."""
    code = "l10n_de_datev_identifier_customer_sequence"
    Sequence = env["ir.sequence"].sudo()
    Partner = env["res.partner"].sudo()
    companies = env["res.company"].search([])

    def _max_identifier(company):
        partner = Partner.with_company(company).search(
            [("l10n_de_datev_identifier_customer", "!=", False)],
            order="l10n_de_datev_identifier_customer desc",
            limit=1,
        )
        return partner.l10n_de_datev_identifier_customer if partner else 0

    for seq in Sequence.search([("code", "=", code)]):
        if seq.company_id:
            max_id = _max_identifier(seq.company_id)
        else:
            max_id = max([_max_identifier(c) for c in companies] or [0])
        if seq.number_next_actual <= max_id:
            seq.write({"number_next": max_id + 1})
