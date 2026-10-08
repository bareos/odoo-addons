from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDeferredRevenueGraph(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.revenue_account = cls.env["account.account"].create(
            {
                "name": "Revenue Deferred Graph",
                "code": "REVDEFG",
                "account_type": "income",
            }
        )
        cls.company.deferred_revenue_journal_id = cls.env["account.journal"].create(
            {
                "name": "Deferred Revenue Journal Graph",
                "code": "DEFG",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.company.deferred_revenue_account_id = cls.company_data[
            "default_account_deferred_revenue"
        ].id
        cls.deferred_account = cls.company.deferred_revenue_account_id

    def _create_deferred_invoice(self, date="2023-01-15", price_unit=1200.0):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "date": date,
                "invoice_date": date,
                "journal_id": self.company_data["default_journal_sale"].id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "account_id": self.revenue_account.id,
                            "price_unit": price_unit,
                            "quantity": 1,
                            "tax_ids": [Command.set([])],
                            "deferred_start_date": date,
                            "deferred_end_date": "2024-04-30",
                        }
                    )
                ],
            }
        )
        move.action_post()
        return move

    def test_action_structure(self):
        action = self.env["account.move.line"].action_deferred_revenue_graph(
            "2023-01-01", "2024-12-31"
        )
        self.assertEqual(action["res_model"], "account.move.line")
        # A real window action id is needed for "Add to my dashboard".
        self.assertEqual(
            action["id"],
            self.env.ref(
                "account_deferred_revenue_graph.action_window_deferred_revenue_graph"
            ).id,
        )
        self.assertIn("graph", action["view_mode"])
        # The graph of the by-month report shows the cumulated provision
        # balance ("Provisions" view), not the booked-back debit.
        self.assertIn(
            (
                self.env.ref(
                    "account_deferred_revenue_graph."
                    "view_account_move_line_deferred_revenue_provisions_graph"
                ).id,
                "graph",
            ),
            action["views"],
        )
        self.assertIn(("account_id", "=", self.deferred_account.id), action["domain"])
        self.assertIn(
            ("move_id.deferred_original_move_ids", "!=", False), action["domain"]
        )
        self.assertIn(("parent_state", "!=", "cancel"), action["domain"])
        self.assertIn(("date", ">=", "2023-01-01"), action["domain"])
        self.assertIn(("date", "<=", "2024-12-31"), action["domain"])

    def test_action_recognized_graph(self):
        """The second rendering opens with the recognized (debit) graph."""
        action = self.env["account.move.line"].action_deferred_revenue_graph(
            graph="recognized"
        )
        self.assertEqual(action["name"], "Deferred Revenue (recognized)")
        self.assertEqual(
            action["id"],
            self.env.ref(
                "account_deferred_revenue_graph."
                "action_window_deferred_revenue_graph_recognized"
            ).id,
        )
        self.assertIn(
            (
                self.env.ref(
                    "account_deferred_revenue_graph."
                    "view_account_move_line_deferred_revenue_graph"
                ).id,
                "graph",
            ),
            action["views"],
        )
        # Same data as the provisions rendering.
        self.assertEqual(
            action["domain"],
            self.env["account.move.line"].action_deferred_revenue_graph()["domain"],
        )

    def test_action_without_range_has_no_date_condition(self):
        action = self.env["account.move.line"].action_deferred_revenue_graph()
        self.assertTrue(
            all(
                not (isinstance(leaf, tuple) and leaf[0] == "date")
                for leaf in action["domain"]
            )
        )

    def test_other_company_lines_excluded(self):
        """Lines of another company on a shared deferred account are ignored.

        The deferred revenue account can be shared between companies; the
        reports must only show the entries of the current company.
        """
        invoice = self._create_deferred_invoice()
        other_company = self.env["res.company"].create({"name": "Other Co"})
        ctx = {"allowed_company_ids": [self.env.company.id, other_company.id]}
        # Share the accounts with the other company; Odoo 19 requires a
        # per-company account code before extending company_ids.
        for account in (self.deferred_account, self.revenue_account):
            account.sudo().with_company(other_company).code = account.code
            account.company_ids += other_company
        other_journal = (
            self.env["account.journal"]
            .with_context(**ctx)
            .create(
                {
                    "name": "Other Deferred Journal",
                    "code": "ODFG",
                    "type": "general",
                    "company_id": other_company.id,
                }
            )
        )
        original = (
            self.env["account.move"]
            .with_context(**ctx)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": other_journal.id,
                    "date": "2023-01-15",
                    "line_ids": [
                        Command.create(
                            {"account_id": self.revenue_account.id, "debit": 100.0}
                        ),
                        Command.create(
                            {"account_id": self.deferred_account.id, "credit": 100.0}
                        ),
                    ],
                }
            )
        )
        original.action_post()
        deferral = (
            self.env["account.move"]
            .with_context(**ctx)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": other_journal.id,
                    "date": "2023-01-31",
                    "deferred_original_move_ids": [Command.set(original.ids)],
                    "line_ids": [
                        Command.create(
                            {"account_id": self.deferred_account.id, "credit": 100.0}
                        ),
                        Command.create(
                            {"account_id": self.revenue_account.id, "debit": 100.0}
                        ),
                    ],
                }
            )
        )
        deferral.action_post()

        action_domain = self.env["account.move.line"].action_deferred_revenue_graph()[
            "domain"
        ]
        lines = self.env["account.move.line"].search(action_domain)
        self.assertFalse(lines & deferral.line_ids)
        # the current company's deferral entries are still shown
        self.assertTrue(invoice.deferred_move_ids.line_ids & lines)

    def test_manual_entry_on_account_excluded(self):
        """A manual journal entry on the deferred account is not part of the
        deferral process and must not be shown in the reports."""
        self._create_deferred_invoice()
        manual = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "date": "2023-02-15",
                "line_ids": [
                    Command.create(
                        {"account_id": self.deferred_account.id, "debit": 50.0}
                    ),
                    Command.create(
                        {"account_id": self.revenue_account.id, "credit": 50.0}
                    ),
                ],
            }
        )
        manual.action_post()
        action_domain = self.env["account.move.line"].action_deferred_revenue_graph()[
            "domain"
        ]
        self.assertFalse(
            manual.line_ids & self.env["account.move.line"].search(action_domain)
        )

    def test_provisions_graph_view(self):
        view = self.env.ref(
            "account_deferred_revenue_graph."
            "view_account_move_line_deferred_revenue_provisions_graph"
        )
        self.assertIn('name="balance"', view.arch)
        self.assertIn('cumulated="True"', view.arch)
        # a date filter must not lose the opening balance
        self.assertIn('cumulated_start="True"', view.arch)

    def test_domain_returns_both_sides_and_nets_to_zero(self):
        move = self._create_deferred_invoice()
        self.assertTrue(move.deferred_move_ids)
        lines = self.env["account.move.line"].search(
            self.env["account.move.line"].action_deferred_revenue_graph()["domain"]
        )
        self.assertTrue(lines)
        self.assertTrue(all(line.account_id == self.deferred_account for line in lines))
        # Both sides of the deferral entries are shown: the initial deferral
        # (credit) and the monthly recognitions (debit, including the future
        # drafts) net to 0.
        balances = lines.mapped("balance")
        self.assertTrue(any(balance < 0 for balance in balances))
        self.assertTrue(any(balance > 0 for balance in balances))
        self.assertAlmostEqual(sum(balances), 0.0, places=2)

    def test_cancelled_deferral_entries_excluded(self):
        move = self._create_deferred_invoice()
        domain = self.env["account.move.line"].action_deferred_revenue_graph()["domain"]
        # Simulate a leftover from an invoice reset/re-post cycle: one
        # deferral entry is cancelled while the invoice stays posted.
        initial = move.deferred_move_ids.filtered(lambda m: m.state == "posted")[:1]
        initial.button_draft()
        initial.button_cancel()
        lines = self.env["account.move.line"].search(domain)
        self.assertFalse(initial.line_ids & lines)

    def test_extra_domain_hook(self):
        # The generic module adds no restriction by default.
        self.assertEqual(
            self.env["account.move.line"]._get_deferred_revenue_graph_extra_domain(),
            [],
        )

    def test_server_actions_runnable_by_readonly_accounting_user(self):
        """A read-only accounting user must be able to open both reports.

        The menus are visible to ``account.group_account_readonly``; the
        server actions they trigger must carry the same group, otherwise
        ``ir.actions.server.run()`` falls back to a write-access check on
        ``account.move.line`` and raises an AccessError for read-only users.
        """
        self._create_deferred_invoice()
        user = self.env["res.users"].create(
            {
                "name": "Readonly Deferred Graph",
                "login": "readonly_deferred_graph",
                "group_ids": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("account.group_account_readonly").id,
                        ]
                    )
                ],
            }
        )
        for xmlid in (
            "action_server_deferred_revenue_graph",
            "action_server_deferred_revenue_graph_recognized",
        ):
            server_action = self.env.ref(f"account_deferred_revenue_graph.{xmlid}")
            action = server_action.with_user(user).run()
            self.assertEqual(action["res_model"], "account.move.line")
            self.assertTrue(
                self.env["account.move.line"]
                .with_user(user)
                .search_count(action["domain"])
            )
