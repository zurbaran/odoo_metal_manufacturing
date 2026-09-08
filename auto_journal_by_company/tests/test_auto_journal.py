from odoo.tests.common import TransactionCase

# TransactionCase en Odoo 18 ejecuta cada método de test dentro de un savepoint,
# por lo que sustituye el uso histórico de SavepointCase.


class TestAutoJournalByCompany(TransactionCase):
    """
    Conjunto de tests para el módulo `auto_journal_by_company`.

    Objetivo:
      - Verificar que la lógica de asignación automática de diarios
        (journals) en `account.move` funciona correctamente:
          * Asigna el diario de ventas adecuado para facturas de cliente.
          * Asigna el diario de compras adecuado para facturas de proveedor.
          * Respeta diarios ya definidos manualmente.
          * Ejecuta correctamente la lógica en el onchange.
    """

    @classmethod
    def setUpClass(cls):
        """
        Configuración inicial que se ejecuta una vez para toda la clase de test.

        Aquí se crean:
          - Una compañía de prueba.
          - Un diario de ventas (`sale`) asociado a esa compañía.
          - Un diario de compras (`purchase`) asociado a esa compañía.

        Estos registros se reutilizarán en todos los métodos de test.
        """
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
