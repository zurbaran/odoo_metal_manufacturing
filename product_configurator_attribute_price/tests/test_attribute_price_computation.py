from odoo.tests.common import TransactionCase


class TestAttributePriceComputation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env["product.attribute"].create(
            {"name": "Largo", "create_variant": "no_variant"}
        )
        cls.attribute_value = cls.env["product.attribute.value"].create(
            {
                "name": "Valor Largo",
                "attribute_id": cls.attribute.id,
                "is_custom": True,
            }
        )
        cls.product_template = cls.env["product.template"].create(
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
        cls.ptav.write(
            {
                "price_formula": "custom_value * 0.5",
                "price_extra": 10.0,
            }
        )
        partner = cls.env["res.partner"].create({"name": "Price Formula Partner"})
        cls.order = cls.env["sale.order"].create({"partner_id": partner.id})

    def test_price_computation_with_formula_and_price_extra(self):
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
                "custom_value": "200",
            }
        )
        line.invalidate_recordset(["product_custom_attribute_value_ids"])
        line.with_context(force_price_recomputation=True)._compute_price_unit()

        expected_price = line.currency_id.round(100 + (200 * 0.5) + 10)
        self.assertEqual(line.price_unit, expected_price)
        self.assertEqual(line.technical_price_unit, expected_price)

    def test_manual_price_is_preserved(self):
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
            }
        )
        line.price_unit = 777.0
        line._compute_price_unit()
        self.assertEqual(line.price_unit, 777.0)
