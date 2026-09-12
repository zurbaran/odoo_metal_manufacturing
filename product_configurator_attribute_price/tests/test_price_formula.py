from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPriceFormula(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        attribute = cls.env["product.attribute"].create(
            {"name": "Formula Attribute", "create_variant": "no_variant"}
        )
        value = cls.env["product.attribute.value"].create(
            {"name": "Formula Value", "attribute_id": attribute.id}
        )
        template = cls.env["product.template"].create(
            {
                "name": "Formula Product",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, [value.id])],
                        },
                    )
                ],
            }
        )
        cls.ptav = template.attribute_line_ids.product_template_value_ids

    def test_calculate_price_increment_formula(self):
        self.ptav.write({"price_formula": "custom_value * 2", "price_extra": 0})
        self.assertEqual(self.ptav.calculate_price_increment(10, 0), 20)

    def test_calculate_price_increment_no_formula(self):
        self.ptav.write({"price_formula": False, "price_extra": 5})
        self.assertEqual(self.ptav.calculate_price_increment(10, 0), 5)

    def test_calculate_price_increment_negative(self):
        self.ptav.write({"price_formula": "custom_value - 50", "price_extra": 0})
        self.assertEqual(self.ptav.calculate_price_increment(10, 0), 0)

    def test_calculate_price_increment_error(self):
        self.ptav.write({"price_formula": "custom_value *** 2", "price_extra": 0})
        with self.assertRaises(ValidationError):
            self.ptav.calculate_price_increment(10, 0)

    def test_math_formula_and_price_so_far(self):
        self.ptav.write(
            {"price_formula": "math.ceil(custom_value / 50) + price_so_far * 0.1"}
        )
        self.assertEqual(self.ptav.calculate_price_increment(101, 100), 13.0)
