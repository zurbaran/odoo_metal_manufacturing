from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintReport(TransactionCase):
    """Comprueba la integración de la acción de impresión de planos."""

    def test_action_print_blueprint(self):
        partner = self.env["res.partner"].create({"name": "Blueprint Report Partner"})
        order = self.env["sale.order"].create({"partner_id": partner.id})

        action = order.action_print_blueprint()

        # En una base nueva Odoo puede abrir primero el asistente de configuración
        # del layout documental. En ese caso conserva la acción real del informe
        # dentro de context['report_action'].
        report_action = action.get("context", {}).get("report_action") or action

        self.assertEqual(
            report_action.get("report_name"),
            "product_blueprint_manager.report_sale_order_blueprint",
        )
        self.assertEqual(report_action.get("report_type"), "qweb-pdf")
