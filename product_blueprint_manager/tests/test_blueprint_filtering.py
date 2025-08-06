from odoo.tests.common import TransactionCase  # pyright: ignore[reportMissingImports]


class TestBlueprintFiltering(TransactionCase):
    def setUp(self):
        super().setUp()
        ProductTemplate = self.env["product.template"]
        Product = self.env["product.product"]  # noqa: F841
        Attribute = self.env["product.attribute"]
        AttributeValue = self.env["product.attribute.value"]
        Blueprint = self.env["product.blueprint"]

        # Crear atributos y valores
        self.attr_vidrio = Attribute.create(
            {
                "name": "Vidrio",
                "create_variant": "no_variant",
            }
        )
        self.val_transp = AttributeValue.create(
            {
                "name": "Transparente",
                "attribute_id": self.attr_vidrio.id,
            }
        )
        self.val_carglas = AttributeValue.create(
            {
                "name": "Impreso Carglas",
                "attribute_id": self.attr_vidrio.id,
            }
        )
        self.attr_acabado = Attribute.create(
            {
                "name": "Acabado",
                "create_variant": "no_variant",
            }
        )
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
        self.product = self.product_template.product_variant_ids[0]

        # Crear blueprint con condición: requiere "Transparente"
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
        """El plano sólo se debe aplicar si TODOS los atributos cumplen"""
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
