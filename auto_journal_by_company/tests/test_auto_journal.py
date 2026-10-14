# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


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
        move = self.env["account.move"].with_company(self.company).create(
            {"move_type": "out_invoice", "company_id": self.company.id}
        )
        self._assert_journal_for(move, "sale")

    def test_auto_journal_purchase_invoice(self):
        move = self.env["account.move"].with_company(self.company).create(
            {"move_type": "in_invoice", "company_id": self.company.id}
        )
        self._assert_journal_for(move, "purchase")

    def test_onchange_auto_assign_journal(self):
        move = self.env["account.move"].with_company(self.company).new(
            {"move_type": "out_invoice", "company_id": self.company.id}
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
        move = self.env["account.move"].with_company(self.company).create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
                "journal_id": other_journal.id,
            }
        )
        self.assertEqual(move.journal_id, other_journal)
