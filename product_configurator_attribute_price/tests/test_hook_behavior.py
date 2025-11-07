from odoo.tests.common import TransactionCase


class TestHookBehavior(TransactionCase):
    def test_hook_returns_attribute_values(self):
        hook = self.env["product.configurator.attribute.hook"]

        attr = self.env["product.attribute"].create({"name": "Color"})
        ptav = self.env["product.template.attribute.value"].create(
            {"name": "Rojo", "attribute_id": attr.id}
        )
        line = self.env["sale.order.line"].create({})
        cav = self.env["product.custom.attribute.value"].create(
            {
                "sale_order_line_id": line.id,
                "custom_product_template_attribute_value_id": ptav.id,
                "custom_value": 123,
            }
        )

        result = hook.get_attribute_values_for_blueprint(line)
        self.assertEqual(result["Color"], cav.eval() if hasattr(cav, "eval") else 123)
