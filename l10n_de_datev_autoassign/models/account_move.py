import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_next_datev_customer_identifier(self):
        """
        Liefert die nächste freie DATEV-Debitorennummer via ir.sequence.
        Gibt einen Integer zurück, da l10n_de_datev_identifier_customer ein Integer-Feld ist.
        """
        sequence_code = 'datev.customer.identifier'
        next_val = self.env['ir.sequence'].next_by_code(sequence_code)

        if not next_val:
            raise UserError(_(
                "Die Sequenz '%s' wurde nicht gefunden. "
                "Bitte prüfen Sie die Modulinstallation oder legen Sie die Sequenz "
                "unter Einstellungen → Technisch → Sequenzen manuell an."
            ) % sequence_code)

        try:
            return int(next_val)
        except (ValueError, TypeError):
            raise UserError(_(
                "Die Sequenz '%s' hat einen ungültigen Wert zurückgegeben: %s. "
                "Bitte stellen Sie sicher, dass kein Prefix/Suffix konfiguriert ist."
            ) % (sequence_code, next_val))

    def action_post(self):
        """
        Überschreibt action_post: Weist Kunden ohne DATEV-Debitorennummer
        automatisch die nächste freie Nummer zu, bevor die Rechnung gebucht wird.
        """
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue

            partner = move.partner_id

            # Nur prüfen wenn Auto-Assign in den Einstellungen aktiv ist
            auto_assign = self.env['ir.config_parameter'].sudo().get_param(
                'l10n_de_datev_autoassign.auto_assign_customer_identifier',
                default='True',
            )
            if auto_assign != 'True':
                continue

            if not partner.l10n_de_datev_identifier_customer:
                next_id = self._get_next_datev_customer_identifier()
                partner.sudo().write({
                    'l10n_de_datev_identifier_customer': next_id
                })
                _logger.info(
                    "DATEV-Debitorennummer %s automatisch gesetzt für Partner '%s' (ID %s) "
                    "beim Bestätigen von Rechnung '%s'.",
                    next_id, partner.name, partner.id, move.name,
                )

        return super().action_post()
