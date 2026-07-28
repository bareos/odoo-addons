import logging

from odoo import models, fields, api

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

    @api.model
    def get_values(self):
        """Get maximum from next sequence number
        and existing l10n_de_datev_identifier_customer numbers.
        """
        res = super().get_values()

        # Nächste Sequenznummer auslesen
        sequence = (
            self.env["ir.sequence"]
            .sudo()
            .search(
                [("code", "=", "l10n_de_datev_identifier_customer_sequence")], limit=1
            )
        )
        next_sequence_number = sequence.number_next_actual if sequence else 0
        _logger.debug(
            "datev_customer_identifier_next next_sequence_number=%s"
            % next_sequence_number
        )
        partner = self.env["res.partner"].search(
            [("l10n_de_datev_identifier_customer", "!=", False)],
            order="l10n_de_datev_identifier_customer desc",
            limit=1,
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

        # Nächste Sequenznummer schreiben wenn geändert
        sequence = (
            self.env["ir.sequence"]
            .sudo()
            .search(
                [("code", "=", "l10n_de_datev_identifier_customer_sequence")], limit=1
            )
        )
        if sequence and self.datev_customer_identifier_next:
            sequence.sudo().write({"number_next": self.datev_customer_identifier_next})
