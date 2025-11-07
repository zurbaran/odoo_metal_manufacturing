from odoo.tests.common import TransactionCase


class TestDescriptionGeneration(TransactionCase):
    def setUp(self):
        super().setUp()

        self.attribute = self.env["product.attribute"].create(
            {"name": "Alto", "create_variant": "no_variant", "is_custom": True}
        )
        self.ptav = self.env["product.template.attribute.value"].create(
            {
                "name": "mmA",
                "attribute_id": self.attribute.id,
            }
        )
        self.product = self.env["product.product"].create({"name": "Mampara Base"})

    def test_description_contains_custom_attribute(self):
        line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_custom_attribute_value_ids": [
                    (
                        0,
                        0,
                        {
                            "custom_product_template_attribute_value_id": self.ptav.id,
                            "custom_value": 1456,
                        },
                    )
                ],
            }
        )
        line._onchange_product_id()
        self.assertIn("Alto: mmA: 1456.0", line.name)
