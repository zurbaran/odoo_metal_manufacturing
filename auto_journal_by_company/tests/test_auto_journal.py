from odoo.tests.common import SavepointCase

# SavepointCase:
#   - Clase base de los tests de Odoo que utiliza transacciones con puntos
#     de guardado (savepoints).
#   - Es más eficiente que TransactionCase para ejecutar múltiples tests
#     sobre la misma base de datos de prueba.


class TestAutoJournalByCompany(SavepointCase):
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
        # Llamada al setUpClass original de SavepointCase para inicializar el entorno
        super().setUpClass()
        # Creación de una compañía de prueba
        cls.company = cls.env["res.company"].create({"name": "Empresa de Test"})
        # Diario de ventas de prueba (tipo `sale`) para la compañía
        cls.journal_sale = cls.env["account.journal"].create(
            {
                "name": "Ventas Test",
                "type": "sale",
                "code": "VT",
                "company_id": cls.company.id,
            }
        )
        # Diario de compras de prueba (tipo `purchase`) para la compañía
        cls.journal_purchase = cls.env["account.journal"].create(
            {
                "name": "Compras Test",
                "type": "purchase",
                "code": "CT",
                "company_id": cls.company.id,
            }
        )

    def test_auto_journal_sale_invoice(self):
        """
        Comprueba que, al crear una factura de cliente (`out_invoice`)
        para la compañía de prueba, se asigna automáticamente el diario
        de ventas (`journal_sale`).

        Flujo:
          - Se crea un `account.move` con `move_type='out_invoice'`
            y `company_id` definido.
          - Se espera que `journal_id` sea el diario de ventas creado
            en `setUpClass`.
        """
        # Creación de una factura de cliente (out_invoice) sin journal explícito
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
            }
        )
        # Verificación: el diario asignado debe ser el diario de ventas
        self.assertEqual(
            move.journal_id,
            self.journal_sale,
            "No se asignó correctamente el diario de ventas",
        )

    def test_auto_journal_purchase_invoice(self):
        """
        Comprueba que, al crear una factura de proveedor (`in_invoice`)
        para la compañía de prueba, se asigna automáticamente el diario
        de compras (`journal_purchase`).

        Flujo:
          - Se crea un `account.move` con `move_type='in_invoice'`
            y `company_id` definido.
          - Se espera que `journal_id` sea el diario de compras creado
            en `setUpClass`.
        """
        # Creación de una factura de proveedor (in_invoice) sin journal explícito
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
            }
        )
        # Verificación: el diario asignado debe ser el diario de compras
        self.assertEqual(
            move.journal_id,
            self.journal_purchase,
            "No se asignó correctamente el diario de compras",
        )

    def test_onchange_auto_assign_journal(self):
        """
        Comprueba que el método onchange `_onchange_company_or_type`
        asigna correctamente el diario de ventas cuando:

          - Se crea un registro nuevo en memoria (`new`).
          - Se establece `move_type='out_invoice'` y `company_id`.
          - Se ejecuta manualmente el onchange.

        Se valida que, tras el onchange, `journal_id` es el diario de ventas.
        """
        # Creación de un registro "en memoria" (no guardado en la BD)
        move = self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
            }
        )
        # Ejecución manual del onchange definido en el modelo
        move._onchange_company_or_type()
        # Verificación: el diario asignado debe ser el diario de ventas
        self.assertEqual(
            move.journal_id,
            self.journal_sale,
            "El onchange no asignó el diario de ventas",
        )

    def test_create_respects_existing_journal(self):
        """
        Comprueba que, al crear un `account.move` indicando explícitamente
        un `journal_id` en los valores, la lógica de auto-asignación
        NO lo sobreescribe.

        Flujo:
          - Se crea un diario adicional de tipo `general`.
          - Se crea un `account.move` con `move_type='out_invoice'`,
            `company_id` definido y `journal_id` establecido a este diario.
          - Se verifica que el movimiento conserva el diario indicado y
            no es reemplazado por el diario de ventas.
        """
        # Creación de un diario adicional (tipo general) para la misma compañía
        other_journal = self.env["account.journal"].create(
            {
                "name": "Misceláneo",
                "type": "general",
                "code": "MI",
                "company_id": self.company.id,
            }
        )
        # Creación de una factura de cliente indicando manualmente journal_id
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": self.company.id,
                "journal_id": other_journal.id,
            }
        )
        # Verificación: el diario debe seguir siendo el que se pasó en vals
        self.assertEqual(
            move.journal_id,
            other_journal,
            "Se reemplazó un diario ya definido",
        )
