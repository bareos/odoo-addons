from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Toggle: Auto-Assign an/aus
    datev_auto_assign_customer_identifier = fields.Boolean(
        string='DATEV-Debitorennummer automatisch vergeben',
        help=(
            'Wenn aktiv, wird beim Bestätigen einer Ausgangsrechnung dem Kunden '
            'automatisch eine DATEV-Debitorennummer zugewiesen, falls noch keine gesetzt ist.'
        ),
        config_parameter='l10n_de_datev_autoassign.auto_assign_customer_identifier',
    )

    # Nächste Nummer direkt hier anzeigen/setzen (Komfort-Feld)
    datev_customer_identifier_next = fields.Integer(
        string='Nächste DATEV-Debitorennummer',
        help='Zeigt und setzt die nächste Nummer der DATEV-Debitorensequenz.',
    )

    @api.model
    def get_values(self):
        res = super().get_values()

        # Nächste Sequenznummer auslesen
        sequence = self.env['ir.sequence'].sudo().search(
            [('code', '=', 'datev.customer.identifier')], limit=1
        )
        res['datev_customer_identifier_next'] = sequence.number_next_actual if sequence else 0

        return res

    def set_values(self):
        super().set_values()

        # Nächste Sequenznummer schreiben wenn geändert
        sequence = self.env['ir.sequence'].sudo().search(
            [('code', '=', 'datev.customer.identifier')], limit=1
        )
        if sequence and self.datev_customer_identifier_next:
            sequence.sudo().write({
                'number_next': self.datev_customer_identifier_next
            })
