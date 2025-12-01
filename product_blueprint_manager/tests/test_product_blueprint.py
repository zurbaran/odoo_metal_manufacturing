import base64  # Biblioteca estándar para operaciones con datos binarios/base64.

# SavepointCase permite que los tests usen transacciones con puntos de guardado
# (rollback parcial), haciendo las pruebas más eficientes en Odoo.
from odoo.tests.common import SavepointCase  # pyright: ignore[reportMissingImports]


class TestProductBlueprint(SavepointCase):
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
        # Producto base para asociar blueprints y atributos.
        cls.product = cls.env["product.template"].create(
            {
                "name": "Test product",
                "type": "consu",
            }
        )
        # Partner genérico para generar pedidos de venta.
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})

    def test_extract_svg_formulas_creates_names(self):
        """
        Verifica que `_extract_svg_formulas` detecta correctamente las fórmulas
        en el SVG y crea registros `product.blueprint.formula.name` con:

        - Nombre de la fórmula (`LENGTH` extraído de {{LENGTH}}).
        - ID del nodo SVG (`id='f1'`).
        - Estilo visual: color (`fill`) y tamaño de fuente (`font-size`).

        Flujo:
        - Se construye un SVG mínimo con un `<text>` que tiene class='odoo-formula'
          y un contenido `{{LENGTH}}`.
        - Se crea un `product.blueprint` con ese archivo.
        - Se ejecuta `_extract_svg_formulas`.
        - Se busca el registro `product.blueprint.formula.name` asociado y se
          comprueba que:
          * Solo hay uno.
          * El `svg_element_id` coincide con el id del nodo (`f1`).
          * El `fill_color` y `font_size` detectados coinciden con el estilo.
        """
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg'>"
            "<text id='f1' class='odoo-formula' style='fill:#ff0000;font-size:14px'>"
            "{{LENGTH}}</text>"
            "</svg>"
        )
        # Creamos el blueprint asociado al producto de prueba.
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Blueprint 1",
                "file": base64.b64encode(svg.encode()),
                "product_id": self.product.id,
                "blueprint_condition_ids": [],
            }
        )
        # Disparar la lógica de extracción de fórmulas sobre el SVG.
        blueprint._extract_svg_formulas()
        # Buscar la fórmula creada para este blueprint.
        formula_name = self.env["product.blueprint.formula.name"].search(
            [
                ("name", "=", "LENGTH"),
                ("blueprint_id", "=", blueprint.id),
            ]
        )
        # Debe haberse creado exactamente una fórmula.
        self.assertEqual(len(formula_name), 1)
        # El ID del nodo SVG debe coincidir con el id del <text> ("f1").
        self.assertEqual(formula_name.svg_element_id, "f1")
        # Debe haber detectado el color de relleno definido en el style.
        self.assertEqual(formula_name.fill_color, "#ff0000")
        # Debe haber detectado el tamaño de fuente definido en el style.
        self.assertEqual(formula_name.font_size, "14px")

    def test_blueprint_applies_only_with_matching_attribute_value(self):
        """
        Comprueba que un plano condicionado por un valor de atributo concreto
        solo se aplica a las variantes que cumplan esa condición.

        Escenario:
        - Se crea un atributo "Size" con dos valores: S y L.
        - Se añade este atributo a la plantilla de producto, generando variantes.
        - Se crea un `product.blueprint` que solo aplica cuando el valor
          del atributo "Size" es "S".
        - Se crean dos líneas de pedido:
          * Una con la variante de tamaño S.
          * Otra con la variante de tamaño L.
        - Se verifica que:
          * Para la variante S, `_get_evaluated_blueprint()` devuelve al menos
            un plano (el blueprint configurado).
          * Para la variante L, `_get_evaluated_blueprint()` devuelve una lista
            vacía, es decir, el plano no se aplica.
        """
        # Definición del atributo "Size" con valores S y L.
        attribute = self.env["product.attribute"].create({"name": "Size"})
        value_s = self.env["product.attribute.value"].create(
            {"name": "S", "attribute_id": attribute.id}
        )
        value_l = self.env["product.attribute.value"].create(
            {"name": "L", "attribute_id": attribute.id}
        )
        # Asignar el atributo a la plantilla de producto, con ambos valores.
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
        # Filtrar las variantes generadas:
        # - variant_s: la que incluye el valor S.
        # - variant_l: la que incluye el valor L.
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
        # SVG mínimo (sin fórmulas, en este test solo importa la condición).
        svg = "<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        # Crear blueprint que solo aplica cuando el atributo "Size" tiene valor "S".
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
        # Crear un pedido de venta con el partner de prueba.
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        # Línea con la variante que cumple la condición (Size = S).
        line_s = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": variant_s.id,
                "product_uom_qty": 1,
            }
        )
        # Línea con la variante que NO cumple la condición (Size = L).
        line_l = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": variant_l.id,
                "product_uom_qty": 1,
            }
        )
        # Para la variante S debe generarse al menos un blueprint evaluado.
        self.assertTrue(line_s._get_evaluated_blueprint())
        # Para la variante L no debe generarse ningún blueprint.
        self.assertEqual(line_l._get_evaluated_blueprint(), [])
