from odoo.tests.common import TransactionCase


class TestDescriptionGeneration(TransactionCase):
    """Tests de la descripción de líneas con valores personalizados."""

    def setUp(self):
        super().setUp()

        self.attribute = self.env["product.attribute"].create(
            {"name": "Alto", "create_variant": "no_variant"}
        )
        self.attribute_value = self.env["product.attribute.value"].create(
            {
                "name": "mmA",
                "attribute_id": self.attribute.id,
                "is_custom": True,
            }
        )
        self.product_template = self.env["product.template"].create(
            {
                "name": "Mampara Base",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attribute.id,
                            "value_ids": [(6, 0, [self.attribute_value.id])],
                        },
                    )
                ],
            }
        )
        self.product = self.product_template.product_variant_id
        self.ptav = self.product_template.attribute_line_ids.product_template_value_ids.filtered(
            lambda value: value.product_attribute_value_id == self.attribute_value
        )
        self.assertEqual(len(self.ptav), 1)

        partner = self.env["res.partner"].create({"name": "Description Test Partner"})
        self.order = self.env["sale.order"].create({"partner_id": partner.id})

    def test_description_contains_custom_attribute(self):
        line = self.env["sale.order.line"].new(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_custom_attribute_value_ids": [
                    (
                        0,
                        0,
                        {
                            "custom_product_template_attribute_value_id": self.ptav.id,
                            "custom_value": "1456",
                        },
                    )
                ],
            }
        )

        line._onchange_product_id()

        self.assertIn("Alto: mmA: 1456", line.name)
