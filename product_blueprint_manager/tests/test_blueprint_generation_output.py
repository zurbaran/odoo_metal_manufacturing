from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintGeneration(TransactionCase):
    def test_attachment_generated(self):
        sale_line = self.env["sale.order.line"].create(
            {
                "product_id": self.env.ref("product.product_product_4").id,
                "order_id": self.env.ref("sale.sale_order_1").id,
                "product_uom_qty": 1,
            }
        )
        blueprints = sale_line._get_evaluated_blueprint()
        self.assertIsInstance(blueprints, list)
        self.assertTrue(all("attachment_id" in b for b in blueprints))
