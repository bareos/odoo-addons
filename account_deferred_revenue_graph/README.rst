Deferred Revenue Reports
========================

Reports based on the **actual journal entries** instead of the pro-rata
projection of the standard Deferred Revenue report.

* **Deferred Revenue (provisions)**: the journal entries on the deferred revenue
  account, i.e. the money **booked back** from the deferred revenue account to
  the income accounts in each calendar month (the monthly recognition entries
  of the deferral journal) plus the initial deferral entries (credit). Both
  sides are shown, so debit and credit balance and the remaining credit
  balance is the provision stock. Future recognition entries are included as
  drafts (auto-post at date), so the report nets to 0 as soon as the
  deferrals are generated. Fixed facts; they do not change with the selected
  period. Provided as graph, pivot (per-month table) and list of the matching
  journal entries. The graph shows the **cumulated provision balance** per
  month; the measures dropdown and the *Cumulative* / *Stacked* toggles in
  the graph toolbar change the rendering.
* **Deferred Revenue (recognized)**: the same data as the provisions report, but
  the graph opens on the amounts **booked back per month** (the debit side).

Usage
-----

Accounting -> Review -> Control -> Regularization Entries:

* **Deferred Revenue (provisions)** and **Deferred Revenue (recognized)**
  open the reports directly. Choose the period with the **Date**
  range filter (start/end) in the search bar; the period only decides which
  months are shown, the values do not change. The
  view switcher toggles graph / list / pivot and the group-by filters break
  the amounts down by **product** or **product category**.

The **Deferred Revenue** report (the standard one) has an extra **Graph**
button that opens the provisions report.

Technical notes
---------------

The by-month report is an ``account.move.line`` action restricted to the
deferral entries on the company's deferred revenue account:

``[('company_id', '=', <current company>), ('account_id', '=', <deferred revenue account>), ('move_id.deferred_original_move_ids', '!=', False), ('parent_state', '!=', 'cancel')]``

The menus open server actions because the domains need values only known at
runtime (the company's deferred revenue account, the extra-domain hook, the
current user/company). Each returned action dict carries the id of a real
``ir.actions.act_window`` (``action_window_deferred_revenue_graph`` /
``action_window_deferred_revenue_graph_recognized``), which is required for
*Add to my dashboard*: the cog-menu entry only shows for window actions, and
a saved dashboard block references that window action while replaying the
domain captured when it was added, so the dynamic conditions are kept.
Both sides of the deferral entries are shown, so debit and credit sum up to 0;
their difference (the sum of ``balance``) is the remaining provision stock.
Cancelled deferral moves are excluded: they are leftovers from invoice
reset/re-post cycles and have no counterpart recognition entries, so they
would break the balance. The provisions graph groups by ``date`` (month),
measures ``balance`` and cumulates it from the beginning; the recognized
graph measures ``debit``. The pivot shows ``debit``, ``credit`` and
``balance`` per month. The dynamic base domain of the reports is defined in
one place, ``account.move.line._get_deferred_revenue_entries_domain``;
additional restrictions can be added by overriding
``account.move.line._get_deferred_revenue_graph_extra_domain``
(e.g. ``bareos_ratocon_addons`` uses it to exclude resold subscriptions).

Dependencies: ``account_accountant`` and ``account_reports`` (Odoo Enterprise).
