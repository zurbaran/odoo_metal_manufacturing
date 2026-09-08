import base64  # Biblioteca estándar para operaciones con datos binarios/base64.

# TransactionCase en Odoo 18 ejecuta cada método de test dentro de un savepoint,
# sustituyendo el uso histórico de SavepointCase.
from odoo.tests.common import TransactionCase  # pyright: ignore[reportMissingImports]


class TestProductBlueprint(TransactionCase):
    """
    Conjunto de tests funcionales para el modelo `product.blueprint`.

    Objetivos principales:
    - Verificar que la extracción de fórmulas desde un SVG crea correctamente
      los registros `product.blueprint.formula.name` y respeta atributos
      visuales detectados (color, tamaño de fuente, id del nodo SVG).
    - Comprobar que las condiciones de plano basadas en atributos de producto
      se aplican correctamente, de manera que solo se generen planos cuando
      los valores de atributo coinciden con la configuración del plano.
    """

    @classmethod
    def setUpClass(cls):
        """
        Configuración inicial compartida por todos los tests de la clase.

        - Crea un producto `product.template` sencillo de tipo consumible.
        - Crea un partner genérico que se usará para crear pedidos de venta
          en los tests.
        """
        super().setUpClass()
        cls.product = cls.env["product.template"].create(
            {
                "name": "Test product",
                "type": "consu",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})

    def test_extract_svg_formulas_creates_names(self):
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
                "product_id": self.product.id,
                "blueprint_condition_ids": [],
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

    def test_blueprint_applies_only_with_matching_attribute_value(self):
        attribute = self.env["product.attribute"].create({"name": "Size"})
        value_s = self.env["product.attribute.value"].create(
            {"name": "S", "attribute_id": attribute.id}
        )
        value_l = self.env["product.attribute.value"].create(
            {"name": "L", "attribute_id": attribute.id}
        )
        self.product.attribute_line_ids = [
            (
                0,
                0,
                {
                    "attribute_id": attribute.id,
                    "value_ids": [(6, 0, [value_s.id, value_l.id])],
                },
            )
        ]
        variant_s = self.product.product_variant_ids.filtered(
            lambda p: value_s
            in p.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            )
        )[0]
        variant_l = self.product.product_variant_ids.filtered(
            lambda p: value_l
            in p.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            )
        )[0]
        svg = "<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        self.env["product.blueprint"].create(
            {
                "name": "Blueprint 2",
                "file": base64.b64encode(svg.encode()),
                "product_id": self.product.id,
                "blueprint_condition_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, [value_s.id])],
                        },
                    )
                ],
            }
        )
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        line_s = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": variant_s.id,
                "product_uom_qty": 1,
            }
        )
        line_l = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": variant_l.id,
                "product_uom_qty": 1,
            }
        )
        self.assertTrue(line_s._get_evaluated_blueprint())
        self.assertEqual(line_l._get_evaluated_blueprint(), [])
