from odoo.tests.common import TransactionCase, tagged

# TransactionCase: clase base de tests que ejecutan transacciones reales
# tagged: permite marcar el test para que se ejecute sólo en ciertos momentos
# (-at_install para no ejecutarlo en la instalación inicial, post_install para después)


@tagged("-at_install", "post_install")
class TestProductBlueprintModels(TransactionCase):
    # Esta clase agrupa tests de alto nivel sobre el modelo `product.blueprint`,
    # enfocándose en:
    # - Extracción automática de fórmulas desde el SVG al crear el blueprint.
    # - Restricción de unicidad de nombres de fórmula por plano (blueprint).

    def test_formula_extraction_on_create(self):
        # Este test verifica que al crear un `product.blueprint` con un SVG que
        # contiene nodos marcados como `class='odoo-formula'`, se generen
        # automáticamente los registros relacionados de nombres de fórmula
        # (`product.blueprint.formula.name`) y se rellene `formula_name_ids`.

        # Creamos un blueprint mínimo con:
        # - product_tmpl_id conocido (plantilla de producto demo de Odoo).
        # - sin condiciones de plano (blueprint_condition_ids vacío).
        # - svg_file con un único nodo <text> que contiene una fórmula "Ancho".
        # - tipo "manufacturing" (plano de fabricación).
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
        # Comprobamos que el campo relacional `formula_name_ids` tenga contenido,
        # lo que implica que se ha ejecutado la lógica de extracción de fórmulas
        # desde el SVG al crear el blueprint.
        self.assertTrue(
            blueprint.formula_name_ids, "La fórmula no se extrajo automáticamente"
        )

    def test_unique_formula_names_per_blueprint(self):
        # Este test comprueba la restricción de unicidad de nombres de fórmula
        # por plano (blueprint). No debería ser posible tener dos fórmulas con
        # el mismo "nombre de etiqueta" (`product.blueprint.formula.name`) para
        # el mismo `product.blueprint`.

        # Creamos un blueprint con un SVG simple que contiene una única fórmula
        # identificada por aria-label='Valor1'.
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
        # Intentamos escribir un nuevo SVG en el mismo blueprint que contenga
        # DOS nodos de fórmula con el mismo aria-label='Valor1'. Esto debería
        # violar la restricción de unicidad (a nivel de modelo o SQL) y lanzar
        # una excepción.
        with self.assertRaises(Exception):  # noqa: B017
            blueprint.write(
                {
                    "svg_file": b"""<svg><text class='odoo-formula'
                      aria-label='Valor1'>0</text>
                      <text class='odoo-formula' aria-label='Valor1'>0</text></svg>"""
                }
            )
