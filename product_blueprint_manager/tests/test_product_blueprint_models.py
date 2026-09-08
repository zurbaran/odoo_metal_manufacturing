import base64

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestProductBlueprintModels(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_template = self.env["product.template"].create(
            {"name": "Producto Blueprint Test"}
        )

    def _create_blueprint(self, name, svg):
        return self.env["product.blueprint"].create(
            {
                "name": name,
                "product_id": self.product_template.id,
                "blueprint_condition_ids": [],
                "file": base64.b64encode(svg),
                "type_blueprint": "manufacturing",
            }
        )

    def test_formula_extraction_on_create(self):
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            b'<text id="formula-ancho" class="odoo-formula">{{Ancho}}</text>'
            b"</svg>"
        )
        blueprint = self._create_blueprint("Plano SVG Test", svg)

        formula_name = self.env["product.blueprint.formula.name"].search(
            [
                ("blueprint_id", "=", blueprint.id),
                ("name", "=", "Ancho"),
                ("svg_element_id", "=", "formula-ancho"),
            ]
        )
        self.assertEqual(
            len(formula_name),
            1,
            "La fórmula no se extrajo automáticamente al crear el blueprint",
        )

    def test_formula_extraction_is_idempotent(self):
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            b'<text id="formula-valor1" class="odoo-formula">{{Valor1}}</text>'
            b"</svg>"
        )
        blueprint = self._create_blueprint("Plano A", svg)

        blueprint._extract_svg_formulas()
        blueprint._extract_svg_formulas()

        formula_names = self.env["product.blueprint.formula.name"].search(
            [
                ("blueprint_id", "=", blueprint.id),
                ("name", "=", "Valor1"),
                ("svg_element_id", "=", "formula-valor1"),
            ]
        )
        self.assertEqual(
            len(formula_names),
            1,
            "Reprocesar el SVG no debe duplicar la misma fórmula/nodo",
        )
