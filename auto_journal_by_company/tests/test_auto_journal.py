# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAutoJournalByCompany(TransactionCase):
    """Check Odoo 19 journal selection without assuming an empty company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Auto Journal Test Company"}
        )
        cls.journal_sale = cls.env["account.journal"].create(
            {
                "name": "Sales journal for tests",
                "type": "sale",
                "code": "AUTS",
                "company_id": cls.company.id,
            }
        )
        cls.journal_purchase = cls.env["account.journal"].create(
            {
                "name": "Purchases journal for tests",
                "type": "purchase",
                "code": "AUTP",
                "company_id": cls.company.id,
            }
        )

    def _assert_journal_for(self, move, journal_type):
        self.assertTrue(move.journal_id)
        self.assertEqual(move.journal_id.company_id, self.company)
        self.assertEqual(move.journal_id.type, journal_type)

    def test_auto_journal_sale_invoice(self):
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .create({"move_type": "out_invoice", "company_id": self.company.id})
        )
        self._assert_journal_for(move, "sale")

    def test_auto_journal_purchase_invoice(self):
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .create({"move_type": "in_invoice", "company_id": self.company.id})
        )
        self._assert_journal_for(move, "purchase")

    def test_onchange_auto_assign_journal(self):
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .new({"move_type": "out_invoice", "company_id": self.company.id})
        )
        move._onchange_company_or_type()
        self._assert_journal_for(move, "sale")

    def test_create_respects_existing_journal(self):
        # Two journals of the same type are valid. A 'general' journal would
        # make this test depend on Odoo's invoice-journal validation.
        other_journal = self.env["account.journal"].create(
            {
                "name": "Alternative sales journal",
                "type": "sale",
                "code": "AUTX",
                "company_id": self.company.id,
            }
        )
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "out_invoice",
                    "company_id": self.company.id,
                    "journal_id": other_journal.id,
                }
            )
        )
        self.assertEqual(move.journal_id, other_journal)

    def test_explicit_company_with_another_active_company(self):
        self.assertNotEqual(self.env.company, self.company)
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
            }
        )
        self._assert_journal_for(move, "sale")

    def test_native_refund_journals(self):
        for move_type, journal_type in [
            ("out_refund", "sale"),
            ("in_refund", "purchase"),
        ]:
            move = (
                self.env["account.move"]
                .with_company(self.company)
                .create(
                    {
                        "move_type": move_type,
                        "company_id": self.company.id,
                    }
                )
            )
            self._assert_journal_for(move, journal_type)

    def test_native_company_change_on_draft_invoice(self):
        other_company = self.env["res.company"].create(
            {"name": "Company switch target"}
        )
        other_journal = self.env["account.journal"].create(
            {
                "name": "Switched sales",
                "code": "SWT",
                "type": "sale",
                "company_id": other_company.id,
            }
        )
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "out_invoice",
                    "company_id": self.company.id,
                }
            )
        )
        with Form(
            move.with_context(allowed_company_ids=[self.company.id, other_company.id])
        ) as form:
            form.company_id = other_company
            self.assertEqual(form.journal_id, other_journal)
        self.assertEqual(move.company_id, other_company)
        self.assertEqual(move.journal_id, other_journal)

    def test_no_journal_keeps_warning_only_helper_behavior(self):
        company = self.env["res.company"].create({"name": "No journal company"})
        move = self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "company_id": company.id,
                "journal_id": False,
            }
        )
        with self.assertLogs(
            "odoo.addons.auto_journal_by_company.models.account_move", level="WARNING"
        ):
            move._auto_assign_journal()
        self.assertFalse(move.journal_id)

    def test_native_journal_for_invoices_from_sale_and_purchase(self):
        if not self.env.registry.get("sale.order") or not self.env.registry.get(
            "purchase.order"
        ):
            self.skipTest("Sale/purchase integration requires those addons installed")
        company = self.company
        Account = self.env["account.account"].with_company(company)
        accounts = {}
        for code, kind in [
            ("AJ701", "income"),
            ("AJ601", "expense"),
            ("AJ411", "asset_receivable"),
            ("AJ401", "liability_payable"),
        ]:
            accounts[kind] = Account.create(
                {
                    "code": code,
                    "name": "Journal regression " + kind,
                    "account_type": kind,
                    "reconcile": kind in ("asset_receivable", "liability_payable"),
                }
            )
        partner = (
            self.env["res.partner"]
            .with_company(company)
            .create(
                {
                    "name": "Invoice source regression partner",
                    "property_account_receivable_id": accounts["asset_receivable"].id,
                    "property_account_payable_id": accounts["liability_payable"].id,
                }
            )
        )
        product = (
            self.env["product.product"]
            .with_company(company)
            .create(
                {
                    "name": "Invoice source service",
                    "type": "service",
                    "invoice_policy": "order",
                    "purchase_method": "purchase",
                    "property_account_income_id": accounts["income"].id,
                    "property_account_expense_id": accounts["expense"].id,
                    "taxes_id": [Command.clear()],
                    "supplier_taxes_id": [Command.clear()],
                }
            )
        )
        warehouse = (
            self.env["stock.warehouse"]
            .with_company(company)
            .create(
                {
                    "name": "Invoice regression warehouse",
                    "code": "AJF",
                }
            )
        )
        order = (
            self.env["sale.order"]
            .with_company(company)
            .create(
                {
                    "partner_id": partner.id,
                    "warehouse_id": warehouse.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "product_uom_qty": 1,
                                "price_unit": 100,
                            }
                        )
                    ],
                }
            )
        )
        order.action_confirm()
        invoices = order._create_invoices()
        self.assertEqual(len(invoices), 1)
        self._assert_journal_for(invoices, "sale")
        purchase = (
            self.env["purchase.order"]
            .with_company(company)
            .create(
                {
                    "partner_id": partner.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "product_qty": 1,
                                "price_unit": 100,
                            }
                        )
                    ],
                }
            )
        )
        purchase.button_confirm()
        purchase.action_create_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        self._assert_journal_for(purchase.invoice_ids, "purchase")
