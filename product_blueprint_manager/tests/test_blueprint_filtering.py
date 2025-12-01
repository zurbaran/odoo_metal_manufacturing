"""Tests de filtrado de planos (product.blueprint) según atributos del producto.

Este módulo valida la lógica que decide qué planos se aplican a una línea de
pedido en función de:
- Los atributos configurados en la plantilla de producto.
- Las condiciones definidas en product.blueprint.condition.
- El tipo de plano (fabricación / purchase).
"""

from odoo.tests.common import TransactionCase  # pyright: ignore[reportMissingImports]


class TestBlueprintFiltering(TransactionCase):
    """Conjunto de pruebas funcionales sobre el filtrado de planos.

    La idea general de estas pruebas es:
    - Construir un entorno mínimo de datos (atributos, valores, producto,
      blueprint).
    - Simular líneas de pedido de venta con distintas combinaciones de
      atributos seleccionados.
    - Comprobar que _get_evaluated_blueprint() devuelve o no cada plano
      según las condiciones definidas.
    """

    def setUp(self):
        """Prepara datos comunes para todos los tests.

        - Crea dos atributos (Vidrio y Acabado) sin generación de variantes
          (create_variant='no_variant').
        - Crea varios valores para esos atributos (Transparente, Impreso Carglas,
          Pulido, Mate).
        - Crea una plantilla de producto que tiene ambos atributos en sus líneas.
        - Crea un blueprint inicial que requiere 'Vidrio: Transparente' como
          condición de aplicación.
        """
        super().setUp()
        # Modelos base utilizados en todas las pruebas
        ProductTemplate = self.env["product.template"]
        Product = self.env["product.product"]  # noqa: F841  # se guarda por claridad, aunque no se usa directamente
        Attribute = self.env["product.attribute"]
        AttributeValue = self.env["product.attribute.value"]
        Blueprint = self.env["product.blueprint"]

        # Crear atributos y valores
        # Atributo de tipo "Vidrio" (no genera variantes por sí mismo)
        self.attr_vidrio = Attribute.create(
            {
                "name": "Vidrio",
                "create_variant": "no_variant",
            }
        )
        # Valor "Transparente" del atributo Vidrio
        self.val_transp = AttributeValue.create(
            {
                "name": "Transparente",
                "attribute_id": self.attr_vidrio.id,
            }
        )
        # Valor "Impreso Carglas" del atributo Vidrio
        self.val_carglas = AttributeValue.create(
            {
                "name": "Impreso Carglas",
                "attribute_id": self.attr_vidrio.id,
            }
        )
        # Atributo de tipo "Acabado" (también sin variantes)
        self.attr_acabado = Attribute.create(
            {
                "name": "Acabado",
                "create_variant": "no_variant",
            }
        )
        # Valores del atributo Acabado
        self.val_pulido = AttributeValue.create(
            {
                "name": "Pulido",
                "attribute_id": self.attr_acabado.id,
            }
        )
        self.val_mate = AttributeValue.create(
            {
                "name": "Mate",
                "attribute_id": self.attr_acabado.id,
            }
        )

        # Crear producto con ambos atributos
        # Se configuran las líneas de atributo para que la plantilla tenga
        # disponibles todos los valores creados arriba.
        self.product_template = ProductTemplate.create(
            {
                "name": "Mampara Test",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_vidrio.id,
                            "value_ids": [
                                (6, 0, [self.val_transp.id, self.val_carglas.id])
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_acabado.id,
                            "value_ids": [
                                (6, 0, [self.val_pulido.id, self.val_mate.id])
                            ],
                        },
                    ),
                ],
            }
        )
        # Primera variante generada a partir de la plantilla
        self.product = self.product_template.product_variant_ids[0]

        # Crear blueprint con condición: requiere "Transparente"
        # Este blueprint solo debería aplicarse cuando la línea de venta
        # tenga seleccionado el valor 'Transparente' para el atributo 'Vidrio'.
        self.blueprint = Blueprint.create(
            {
                "name": "Plano Transparente",
                "type": "purchase",
                "product_tmpl_id": self.product_template.id,
                "blueprint_condition_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_vidrio.id,
                            "value_ids": [(6, 0, [self.val_transp.id])],
                        },
                    )
                ],
                "svg_file": b"<svg></svg>",
            }
        )

    def test_blueprint_is_included_when_attribute_matches(self):
        """El plano debe incluirse cuando la línea cumple la condición.

        Caso:
        - La línea de venta tiene como valor de 'Vidrio' → 'Transparente'.
        - El blueprint tiene condición sobre 'Vidrio' = 'Transparente'.
        Resultado esperado:
        - El blueprint "Plano Transparente" aparece en la lista devuelta por
          _get_evaluated_blueprint().
        """
        # Simula línea con valor "Transparente"
        order_line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [(6, 0, [self.val_transp.id])],
            }
        )
        result = order_line._get_evaluated_blueprint(type_blueprint="purchase")
        names = [b["blueprint_name"] for b in result]
        self.assertIn("Plano Transparente", names, "El plano debería incluirse")

    def test_blueprint_is_excluded_when_attribute_does_not_match(self):
        """El plano no debe incluirse cuando la condición no se cumple.

        Caso:
        - La línea de venta tiene 'Vidrio' = 'Impreso Carglas'.
        - El blueprint exige 'Vidrio' = 'Transparente'.
        Resultado esperado:
        - El blueprint "Plano Transparente" NO aparece en la lista.
        """
        # Simula línea con valor "Impreso Carglas"
        order_line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [(6, 0, [self.val_carglas.id])],
            }
        )
        result = order_line._get_evaluated_blueprint(type_blueprint="purchase")
        names = [b["blueprint_name"] for b in result]
        self.assertNotIn("Plano Transparente", names, "El plano no debe incluirse")

    def test_blueprint_without_conditions_applies(self):
        """Los planos sin condiciones deben aplicarse siempre.

        Caso:
        - Se crea un nuevo blueprint "Plano Libre" sin condiciones.
        - La línea de venta tiene un valor cualquiera.
        Resultado esperado:
        - "Plano Libre" aparece en la lista resultante.
        """
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano Libre",
                "type": "purchase",
                "product_tmpl_id": self.product_template.id,
                "blueprint_condition_ids": [],
                "svg_file": b"<svg></svg>",
            }
        )
        order_line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [(6, 0, [self.val_carglas.id])],
            }
        )
        result = order_line._get_evaluated_blueprint(type_blueprint="purchase")
        names = [b["blueprint_name"] for b in result]
        self.assertIn(blueprint.name, names, "El plano sin condiciones debe incluirse")

    def test_blueprint_with_multiple_conditions(self):
        """Todas las condiciones de un plano deben cumplirse para aplicarlo.

        Caso:
        - Blueprint "Plano Múltiple" exige:
          * Vidrio = Transparente
          * Acabado = Pulido
        - Se crean dos líneas:
          * line_ok: Vidrio = Transparente, Acabado = Pulido → debe incluirse.
          * line_fail: solo Vidrio = Transparente → no debe incluirse.
        """
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano Múltiple",
                "type": "purchase",
                "product_tmpl_id": self.product_template.id,
                "blueprint_condition_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_vidrio.id,
                            "value_ids": [(6, 0, [self.val_transp.id])],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_acabado.id,
                            "value_ids": [(6, 0, [self.val_pulido.id])],
                        },
                    ),
                ],
                "svg_file": b"<svg></svg>",
            }
        )
        # Línea que cumple ambas condiciones: Vidrio=Transparente, Acabado=Pulido
        line_ok = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [
                    (6, 0, [self.val_transp.id, self.val_pulido.id])
                ],
            }
        )
        names_ok = [
            b["blueprint_name"]
            for b in line_ok._get_evaluated_blueprint(type_blueprint="purchase")
        ]
        self.assertIn(
            blueprint.name,
            names_ok,
            "El plano debería incluirse con todas las condiciones",
        )

        # Línea que no cumple todas las condiciones (falta Acabado=Pulido)
        line_fail = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [(6, 0, [self.val_transp.id])],
            }
        )
        names_fail = [
            b["blueprint_name"]
            for b in line_fail._get_evaluated_blueprint(type_blueprint="purchase")
        ]
        self.assertNotIn(
            blueprint.name,
            names_fail,
            "El plano no debe incluirse si falta una condición",
        )

    def test_blueprint_with_multiple_attribute_conditions_must_all_match(self):
        """El plano sólo se debe aplicar si TODOS los atributos cumplen.

        Este test es similar al anterior, pero usando type='manufacturing'
        para comprobar que la lógica de filtrado funciona igual con otro tipo
        de plano.

        Caso:
        - Plano "Plano MultiAtributo" para fabricación con dos condiciones:
          * Vidrio = Transparente
          * Acabado = Pulido
        - line_ok cumple ambos atributos.
        - line_fail sólo cumple uno.
        """
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano MultiAtributo",
                "type": "manufacturing",
                "product_tmpl_id": self.product_template.id,
                "blueprint_condition_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_vidrio.id,
                            "value_ids": [(6, 0, [self.val_transp.id])],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attr_acabado.id,
                            "value_ids": [(6, 0, [self.val_pulido.id])],
                        },
                    ),
                ],
                "svg_file": b"<svg></svg>",
            }
        )
        # Cumple ambos atributos → debe incluirse
        line_ok = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [
                    (6, 0, [self.val_transp.id, self.val_pulido.id])
                ],
            }
        )
        result = line_ok._get_evaluated_blueprint(type_blueprint="manufacturing")
        names_ok = [b["blueprint_name"] for b in result]
        self.assertIn(blueprint.name, names_ok)

        # Falta uno → no debe incluirse
        line_fail = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [(6, 0, [self.val_transp.id])],
            }
        )
        result_fail = line_fail._get_evaluated_blueprint(type_blueprint="manufacturing")
        names_fail = [b["blueprint_name"] for b in result_fail]
        self.assertNotIn(blueprint.name, names_fail)
