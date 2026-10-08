# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Deferred Revenue by Month (Graph)",
    "version": "19.0.1.0.16",
    "summary": "Deferred revenue reports based on the actual journal entries",
    "author": "Bareos GmbH & Co. KG",
    "website": "https://www.bareos.com",
    "category": "Accounting/Accounting",
    "license": "LGPL-3",
    "depends": [
        # deferred revenue report and account.move.deferred_original_move_ids
        "account_accountant",
        # Deferred Revenue report (account.deferred.revenue.report.handler)
        "account_reports",
    ],
    "data": [
        "views/account_move_line_views.xml",
        "views/account_deferred_revenue_graph_actions.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
