import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_next_l10n_de_datev_identifier_customer(self):
        """
        Liefert die nächste freie DATEV-Debitorennummer via ir.sequence.
        Gibt einen Integer zurück, da l10n_de_datev_identifier_customer ein Integer-Feld ist.
        """
        sequence_code = "l10n_de_datev_identifier_customer_sequence"
        next_val = self.env["ir.sequence"].next_by_code(sequence_code)

        if not next_val:
            raise UserError(
                _(
                    "Die Sequenz '%s' wurde nicht gefunden. "
                    "Bitte prüfen Sie die Modulinstallation oder legen Sie die Sequenz "
                    "unter Einstellungen → Technisch → Sequenzen manuell an."
                )
                % sequence_code
            )

        try:
            return int(next_val)
        except (ValueError, TypeError):
            raise UserError(
                _(
                    "Die Sequenz '%s' hat einen ungültigen Wert zurückgegeben: %s. "
                    "Bitte stellen Sie sicher, dass kein Prefix/Suffix konfiguriert ist."
                )
                % (sequence_code, next_val)
            )

    def action_post(self):
        """
        Überschreibt action_post: Weist Kunden ohne DATEV-Debitorennummer
        automatisch die nächste freie Nummer zu, bevor die Rechnung gebucht wird.
        """

        # only if auto-assign is enabled in the settings
        auto_assign = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_de_datev_autoassign.auto_assign_customer_identifier")
        )
        if auto_assign == "True":
            for move in self:
                if move.move_type not in ("out_invoice", "out_refund"):
                    continue

                # get company (commercial_partner_id)
                partner = move.partner_id.commercial_partner_id
                if not partner.l10n_de_datev_identifier_customer:
                    next_id = self._get_next_l10n_de_datev_identifier_customer()
                    while (
                        self.env["res.partner"]
                        .sudo()
                        .search_count(
                            [("l10n_de_datev_identifier_customer", "=", next_id)]
                        )
                    ):
                        next_id = self._get_next_l10n_de_datev_identifier_customer()
                    partner.sudo().write({"l10n_de_datev_identifier_customer": next_id})
                    _logger.info(
                        "Auto-assign DateV Customer number %s "
                        "to partner '%s' (ID %s) "
                        "on confirming invoice with ID %s.",
                        next_id,
                        partner.name,
                        partner.id,
                        move.id,
                    )

        return super().action_post()
