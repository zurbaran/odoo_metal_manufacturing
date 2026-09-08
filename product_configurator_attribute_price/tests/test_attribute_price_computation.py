from odoo.tests.common import TransactionCase


class TestAttributePriceComputation(TransactionCase):
    """Tests del cálculo de precio con valores personalizados y fórmulas."""

    def setUp(self):
        super().setUp()

        # En Odoo 18 ``is_custom`` pertenece al valor del atributo (PAV), no al
        # atributo. El PTAV se materializa al añadir el valor a una línea del
        # producto, igual que ocurre en el configurador real.
        self.attribute = self.env["product.attribute"].create(
            {"name": "Largo", "create_variant": "no_variant"}
        )
        self.attribute_value = self.env["product.attribute.value"].create(
            {
                "name": "Valor Largo",
                "attribute_id": self.attribute.id,
                "is_custom": True,
            }
        )
        self.product_template = self.env["product.template"].create(
            {
                "name": "Producto Base",
                "type": "consu",
                "list_price": 100.0,
                "standard_price": 80.0,
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
        self.ptav.write(
            {
                "price_formula": "custom_value * 0.5",
                "price_extra": 10.0,
            }
        )

        partner = self.env["res.partner"].create({"name": "Price Formula Partner"})
        self.order = self.env["sale.order"].create({"partner_id": partner.id})

    def test_price_computation_with_formula_and_price_extra(self):
        line = self.env["sale.order.line"].new(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "product_custom_attribute_value_ids": [
                    (
                        0,
                        0,
                        {
                            "custom_product_template_attribute_value_id": self.ptav.id,
                            "custom_value": "200",
                        },
                    )
                ],
            }
        )

        line._onchange_product_id()

        expected_price = 100 + (200 * 0.5) + 10
        self.assertEqual(line.price_unit, line.currency_id.round(expected_price))
