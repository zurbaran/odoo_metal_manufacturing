# test_attribute_price_computation.py

from odoo.tests.common import TransactionCase


class TestAttributePriceComputation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_template = self.env.ref(
            "product.product_product_4_product_template"
        )
        self.attribute = self.env["product.attribute"].create(
            {
                "name": "Largo",
                "create_variant": "no_variant",
                "is_custom": True,
            }
        )
        self.value = self.env["product.attribute.value"].create(
            {
                "name": "Largo personalizado",
                "attribute_id": self.attribute.id,
            }
        )
        self.custom_name = self.env["product.blueprint.formula.name"].create(
            {
                "name": "custom_value",
                "attribute_id": self.attribute.id,
                "default_value": "100",
            }
        )

    def test_price_computation_with_formula(self):
        product = self.product_template.product_variant_id
        line = self.env["sale.order.line"].new(
            {
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "product_custom_attribute_value_ids": [
                    (
                        0,
                        0,
                        {
                            "custom_product_template_attribute_value_id": self.value.id,
                            "custom_value": 250,
                        },
                    )
                ],
            }
        )
        line.product_id_change()
        self.assertGreater(
            line.price_unit, 0.0, "El precio no fue recalculado correctamente"
        )
