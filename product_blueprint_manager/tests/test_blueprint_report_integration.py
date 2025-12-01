from odoo.tests.common import TransactionCase, tagged

# =============================================================================
# Tests de integración del reporte de planos (blueprints) en sale.order
#
# Este fichero valida que:
#   - La acción de impresión de planos está correctamente disponible en el
#     modelo `sale.order`.
#   - La acción devuelve un diccionario de acción de informe con la clave
#     `report_name`.
#   - El nombre técnico del reporte contiene la cadena esperada
#     ("blueprint_fabrication_report"), lo que garantiza que el binding del
#     informe está correctamente configurado.
# =============================================================================


@tagged("-at_install", "post_install")
class TestBlueprintReport(TransactionCase):
    """
    Clase de tests para comprobar la integración del botón/acción de impresión
    de planos en los pedidos de venta.
    """

    def test_action_print_blueprint(self):
        """
        Verifica que la acción `action_print_blueprint`:

        - Está disponible en el modelo `sale.order`.
        - Devuelve un diccionario de acción que incluye la clave `report_name`.
        - El valor de `report_name` contiene el identificador esperado del
          informe de planos de fabricación.

        Esto asegura que el reporte está correctamente definido y vinculado.
        """
        # Crear un pedido de venta mínimo usando un partner de datos de demo
        order = self.env["sale.order"].create(
            {"partner_id": self.env.ref("base.res_partner_1").id}
        )

        # Ejecutar la acción de impresión de plano de fabricación
        action = order.action_print_blueprint()

        # Comprobar que la acción contiene el nombre del reporte
        self.assertIn("report_name", action)

        # Comprobar que el nombre del reporte incluye la cadena esperada
        # (identificador técnico del informe de planos de fabricación)
        self.assertIn("blueprint_fabrication_report", action["report_name"])
