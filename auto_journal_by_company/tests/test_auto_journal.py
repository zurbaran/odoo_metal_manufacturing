from odoo.tests import TransactionCase


class TestAutoJournalByCompany(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env["res.company"].create(
            {
                "name": "Empresa de Test",
            }
        )
        self.journal_sale = self.env["account.journal"].create(
            {
                "name": "Ventas Test",
                "type": "sale",
                "code": "VT",
                "company_id": self.company.id,
            }
        )
        self.journal_purchase = self.env["account.journal"].create(
            {
                "name": "Compras Test",
                "type": "purchase",
                "code": "CT",
                "company_id": self.company.id,
            }
        )

    def test_auto_journal_sale_invoice(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
            }
        )
        self.assertEqual(
            move.journal_id,
            self.journal_sale,
            "No se asignó correctamente el diario de ventas",
        )

    def test_auto_journal_purchase_invoice(self):
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
            }
        )
        self.assertEqual(
            move.journal_id,
            self.journal_purchase,
            "No se asignó correctamente el diario de compras",
        )
