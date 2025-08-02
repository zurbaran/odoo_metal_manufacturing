import base64

from odoo.tests.common import TransactionCase


class TestProductBlueprint(TransactionCase):
    def test_extract_svg_formulas_creates_names(self):
        product = self.env["product.template"].create(
            {
                "name": "Test product",
                "type": "consu",
            }
        )
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg'>"
            "<text id='f1' class='odoo-formula' style='fill:#ff0000;font-size:14px'>"
            "{{LENGTH}}</text>"
            "</svg>"
        )
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Blueprint 1",
                "file": base64.b64encode(svg.encode()),
                "product_id": product.id,
            }
        )
        blueprint._extract_svg_formulas()
        formula_name = self.env["product.blueprint.formula.name"].search(
            [
                ("name", "=", "LENGTH"),
                ("blueprint_id", "=", blueprint.id),
            ]
        )
        self.assertEqual(len(formula_name), 1)
        self.assertEqual(formula_name.svg_element_id, "f1")
        self.assertEqual(formula_name.fill_color, "#ff0000")
        self.assertEqual(formula_name.font_size, "14px")
