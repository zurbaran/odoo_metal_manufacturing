from odoo.tests.common import SavepointCase


class TestAutoJournalByCompany(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Empresa de Test"})
        cls.journal_sale = cls.env["account.journal"].create(
            {
                "name": "Ventas Test",
                "type": "sale",
                "code": "VT",
                "company_id": cls.company.id,
            }
        )
        cls.journal_purchase = cls.env["account.journal"].create(
            {
                "name": "Compras Test",
                "type": "purchase",
                "code": "CT",
                "company_id": cls.company.id,
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

    def test_onchange_auto_assign_journal(self):
        move = self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
            }
        )
        move._onchange_company_or_type()
        self.assertEqual(
            move.journal_id,
            self.journal_sale,
            "El onchange no asignó el diario de ventas",
        )

    def test_create_respects_existing_journal(self):
        other_journal = self.env["account.journal"].create(
            {
                "name": "Misceláneo",
                "type": "general",
                "code": "MI",
                "company_id": self.company.id,
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
                "journal_id": other_journal.id,
            }
        )
        self.assertEqual(
            move.journal_id,
            other_journal,
            "Se reemplazó un diario ya definido",
        )
