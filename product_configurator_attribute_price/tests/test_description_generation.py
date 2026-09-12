from odoo.tests.common import TransactionCase


class TestDescriptionGeneration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env["product.attribute"].create(
            {"name": "Alto", "create_variant": "no_variant"}
        )
        cls.attribute_value = cls.env["product.attribute.value"].create(
            {
                "name": "mmA",
                "attribute_id": cls.attribute.id,
                "is_custom": True,
            }
        )
        cls.product_template = cls.env["product.template"].create(
            {
                "name": "Mampara Base",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [(6, 0, [cls.attribute_value.id])],
                        },
                    )
                ],
            }
        )
        cls.product = cls.product_template.product_variant_id
        cls.ptav = cls.product_template.attribute_line_ids.product_template_value_ids.filtered(
            lambda value: value.product_attribute_value_id == cls.attribute_value
        )
        partner = cls.env["res.partner"].create({"name": "Description Test Partner"})
        cls.order = cls.env["sale.order"].create({"partner_id": partner.id})

    def test_description_contains_custom_attribute(self):
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
            }
        )
        self.env["product.attribute.custom.value"].create(
            {
                "sale_order_line_id": line.id,
                "custom_product_template_attribute_value_id": self.ptav.id,
                "custom_value": "1456",
            }
        )
        line.invalidate_recordset(["product_custom_attribute_value_ids"])
        line._compute_name()

        self.assertIn("Alto: mmA: 1456", line.name)
