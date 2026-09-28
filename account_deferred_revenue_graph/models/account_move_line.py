from odoo import _, api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _get_deferred_revenue_graph_extra_domain(self):
        """Hook for modules to further restrict the entries shown.

        Override this (e.g. to exclude resold subscriptions in
        bareos_ratocon_addons) and return additional domain conditions for
        the ``account.move.line`` records the report shows.
        """
        return []

    @api.model
    def _get_deferred_revenue_entries_domain(self):
        """Base domain shared by the deferred revenue reports: the deferral
        entries of the current company on its deferred revenue account.

        This is the single definition of the report domain; everything
        shown by the reports must go through it. Extend it via the
        ``_get_deferred_revenue_graph_extra_domain`` hook instead of
        overriding this method.
        """
        return [
            ("company_id", "=", self.env.company.id),
            ("account_id", "=", self.env.company.deferred_revenue_account_id.id),
            ("move_id.deferred_original_move_ids", "!=", False),
            # Cancelled deferral moves (e.g. leftovers from invoice
            # reset/re-post cycles) have no counterpart recognition entries
            # and would break the debit/credit balance of the report.
            ("parent_state", "!=", "cancel"),
            *self._get_deferred_revenue_graph_extra_domain(),
        ]

    @api.model
    def action_deferred_revenue_graph(
        self, date_from=None, date_to=None, graph="provisions"
    ):
        """Open the Deferred Revenue report.

        The report is based on the actual deferral journal entries on the
        company's deferred revenue account: the initial deferral entries
        (credit) and the monthly recognition entries (debit, booked back
        from the deferred revenue account to income). Both sides are shown,
        so debit and credit balance; the remaining credit balance is the
        provision stock. Future recognition entries are included as drafts
        (auto-post at date), so the report nets to 0 as soon as the
        deferrals are generated. The graph groups them by month, the pivot
        is the per-month table, and the list shows the individual journal
        entries. ``date_from``/``date_to`` narrow the timeframe; unlike the
        Deferred Revenue report the amounts themselves are fixed and do not
        change with the selected range.

        ``graph`` selects the default graph rendering: ``provisions`` (the
        cumulated provision balance, the default) or ``recognized`` (the
        amounts booked back per month). Both renderings share the same data;
        an action can only bind one graph view, which is why the two
        renderings get their own menus/window actions.

        The domain is defined once in
        ``_get_deferred_revenue_entries_domain`` because it references values
        only known at runtime (the company's deferred revenue account, the
        extra-domain hook).
        """
        domain = self._get_deferred_revenue_entries_domain()
        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        if graph == "recognized":
            window_xmlid = "action_window_deferred_revenue_graph_recognized"
            graph_view_xmlid = "view_account_move_line_deferred_revenue_graph"
            name = _("Deferred Revenue (recognized)")
        else:
            window_xmlid = "action_window_deferred_revenue_graph"
            graph_view_xmlid = (
                "view_account_move_line_deferred_revenue_provisions_graph"
            )
            name = _("Deferred Revenue (provisions)")
        return {
            # The id of the real ir.actions.act_window behind this report:
            # without it the "Add to my dashboard" entry does not show up in
            # the cog menu, and a saved dashboard block would have no action
            # to reference. The dynamic domain above still wins over the
            # static domain of the window action.
            "id": self.env.ref(f"account_deferred_revenue_graph.{window_xmlid}").id,
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "account.move.line",
            "view_mode": "graph,list,pivot",
            "views": [
                (
                    self.env.ref(
                        f"account_deferred_revenue_graph.{graph_view_xmlid}"
                    ).id,
                    "graph",
                ),
                (
                    self.env.ref(
                        "account_deferred_revenue_graph."
                        "view_account_move_line_deferred_revenue_list"
                    ).id,
                    "list",
                ),
                (
                    self.env.ref(
                        "account_deferred_revenue_graph."
                        "view_account_move_line_deferred_revenue_pivot"
                    ).id,
                    "pivot",
                ),
            ],
            "search_view_id": self.env.ref(
                "account_deferred_revenue_graph."
                "view_account_move_line_deferred_revenue_search"
            ).id,
            "domain": domain,
        }
