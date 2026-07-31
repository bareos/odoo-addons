{
    "name": "Germany - Accounting - auto create datev_identifier_customer",
    "version": "19.0.1.0.1",
    "summary": "Setzt l10n_de_datev_identifier_customer automatisch beim Bestätigen einer Rechnung.",
    "description": """
        Weist Kunden ohne DATEV-Debitorennummer beim Bestätigen einer Ausgangsrechnung
        automatisch die nächste freie Nummer aus der konfigurierbaren ir.sequence zu.
    """,
    "author": "Bareos GmbH & Co. KG",
    "website": "https://www.bareos.com",
    "category": "Accounting/Localizations",
    "license": "LGPL-3",
    "depends": [
        "account",
        "l10n_de_reports",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "auto_install": False,
    "application": False,
}
