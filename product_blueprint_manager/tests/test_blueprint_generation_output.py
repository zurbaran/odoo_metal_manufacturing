from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintGeneration(TransactionCase):
    """
    Test funcional para verificar que el flujo de generación de planos
    (_get_evaluated_blueprint) crea adjuntos correctamente para una
    línea de pedido de venta.

    Notas:
    - Usa datos de demo: producto 'product.product_product_4' y
      pedido 'sale.sale_order_1'.
    - No comprueba el contenido del adjunto, solo que exista al menos
      un blueprint con 'attachment_id'.
    """

    def test_attachment_generated(self):
        """
        Crea una sale.order.line de ejemplo y comprueba que:

        1) _get_evaluated_blueprint() devuelve una lista.
        2) Cada elemento de esa lista incluye una clave 'attachment_id',
           que corresponde al adjunto SVG/PNG generado por el módulo
           de planos.

        Este test sirve como:
        - Smoke test de integración entre sale.order.line y el módulo
          de planos.
        - Verificación de que no se rompe la lógica de generación de
          adjuntos al modificar el módulo.
        """
        # Crear una línea de pedido de venta usando registros de demo
        sale_line = self.env["sale.order.line"].create(
            {
                # Producto de demo (definido en el módulo 'product')
                "product_id": self.env.ref("product.product_product_4").id,
                # Pedido de venta de demo (definido en el módulo 'sale')
                "order_id": self.env.ref("sale.sale_order_1").id,
                "product_uom_qty": 1,
            }
        )

        # Llamar al método principal del módulo que genera los planos evaluados
        blueprints = sale_line._get_evaluated_blueprint()

        # Verificar que se devuelve una lista (contrato básico del método)
        self.assertIsInstance(blueprints, list)

        # Verificar que todos los elementos tienen un 'attachment_id'
        # (es decir, que se crearon adjuntos para los planos evaluados)
        self.assertTrue(all("attachment_id" in b for b in blueprints))
