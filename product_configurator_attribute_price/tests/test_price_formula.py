from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestPriceFormula(SavepointCase):
    def test_calculate_price_increment_formula(self):
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Length",
                "price_formula": "custom_value * 2",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(10, 0), 20)

    def test_calculate_price_increment_no_formula(self):
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Width",
                "price_formula": False,
                "price_extra": 5,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(10, 0), 5)

    def test_calculate_price_increment_negative(self):
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Size",
                "price_formula": "custom_value - 50",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(10, 0), 0)

    def test_calculate_price_increment_error(self):
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Broken",
                "price_formula": "custom_value /",
                "price_extra": 0,
            }
        )
        with self.assertRaises(ValidationError):
            ptav.calculate_price_increment(10, 0)

    def test_calculate_price_increment_math_functions(self):
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Root",
                "price_formula": "sqrt(custom_value)",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(9, 0), 3)

    def test_calculate_price_increment_uses_price_so_far(self):
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Percent",
                "price_formula": "price_so_far * 0.1",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(10, 100), 10)
