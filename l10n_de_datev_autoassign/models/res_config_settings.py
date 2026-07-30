import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Toggle: Auto-Assign an/aus
    datev_auto_assign_customer_identifier = fields.Boolean(
        string="DATEV-Debitorennummer automatisch vergeben",
        help=(
            "Wenn aktiv, wird beim Bestätigen einer Ausgangsrechnung dem Kunden "
            "automatisch eine DATEV-Debitorennummer zugewiesen, falls noch keine gesetzt ist."
        ),
        config_parameter="l10n_de_datev_autoassign.auto_assign_customer_identifier",
    )

    # Nächste Nummer direkt hier anzeigen/setzen (Komfort-Feld)
    datev_customer_identifier_next = fields.Integer(
        string="Nächste DATEV-Debitorennummer",
        help="Zeigt und setzt die nächste Nummer der DATEV-Debitorensequenz.",
    )

    def _get_datev_sequence(self):
        """Return the company-specific sequence or fall back to the global one."""
        code = "l10n_de_datev_identifier_customer_sequence"
        seq = (
            self.env["ir.sequence"]
            .sudo()
            .search(
                [("code", "=", code), ("company_id", "=", self.env.company.id)],
                limit=1,
            )
        )
        if not seq:
            seq = (
                self.env["ir.sequence"]
                .sudo()
                .search([("code", "=", code), ("company_id", "=", False)], limit=1)
            )
        return seq

    @api.model
    def get_values(self):
        """Get maximum from next sequence number
        and existing l10n_de_datev_identifier_customer numbers.
        """
        res = super().get_values()

        sequence = self._get_datev_sequence()
        next_sequence_number = sequence.number_next_actual if sequence else 0
        _logger.debug(
            "datev_customer_identifier_next next_sequence_number=%s"
            % next_sequence_number
        )
        partner = (
            self.env["res.partner"]
            .sudo()
            .search(
                [("l10n_de_datev_identifier_customer", "!=", False)],
                order="l10n_de_datev_identifier_customer desc",
                limit=1,
            )
        )
        max_l10n_de_datev_identifier_customer = (
            partner.l10n_de_datev_identifier_customer if partner else 0
        )
        _logger.debug(
            "datev_customer_identifier_next l10n_de_datev_identifier_customer=%s"
            % max_l10n_de_datev_identifier_customer
        )

        res["datev_customer_identifier_next"] = max(
            next_sequence_number, max_l10n_de_datev_identifier_customer + 1
        )
        _logger.debug(
            "datev_customer_identifier_next=%s" % res["datev_customer_identifier_next"]
        )

        return res

    def set_values(self):
        """Write the next DATEV customer identifier to the sequence."""
        super().set_values()

        if not self.datev_customer_identifier_next:
            return

        max_partner = (
            self.env["res.partner"]
            .sudo()
            .search(
                [("l10n_de_datev_identifier_customer", "!=", False)],
                order="l10n_de_datev_identifier_customer desc",
                limit=1,
            )
        )
        max_identifier = (
            max_partner.l10n_de_datev_identifier_customer if max_partner else 0
        )
        if self.datev_customer_identifier_next <= max_identifier:
            raise UserError(
                _(
                    "Die nächste DATEV-Debitorennummer (%s) muss größer sein "
                    "als die höchste bereits vergebene Nummer (%s)."
                )
                % (self.datev_customer_identifier_next, max_identifier)
            )

        sequence = self._get_datev_sequence()
        if sequence:
            sequence.sudo().write({"number_next": self.datev_customer_identifier_next})
