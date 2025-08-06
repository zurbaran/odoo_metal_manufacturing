from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestProductBlueprintModels(TransactionCase):
    def test_formula_extraction_on_create(self):
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano SVG Test",
                "product_tmpl_id": self.env.ref(
                    "product.product_product_4_product_template"
                ).id,
                "blueprint_condition_ids": [],
                "svg_file": b"""<svg><text class='odoo-formula' aria-label=
                'Ancho'>0</text></svg>""",
                "type": "manufacturing",
            }
        )
        self.assertTrue(
            blueprint.formula_name_ids, "La fórmula no se extrajo automáticamente"
        )

    def test_unique_formula_names_per_blueprint(self):
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano A",
                "product_tmpl_id": self.env.ref(
                    "product.product_product_4_product_template"
                ).id,
                "blueprint_condition_ids": [],
                "svg_file": b"""<svg><text class='odoo-formula'
                  aria-label='Valor1'>0</text></svg>""",
                "type": "manufacturing",
            }
        )
        with self.assertRaises(Exception):  # noqa: B017
            blueprint.write(
                {
                    "svg_file": b"""<svg><text class='odoo-formula'
                      aria-label='Valor1'>0</text>
                      <text class='odoo-formula' aria-label='Valor1'>0</text></svg>"""
                }
            )
