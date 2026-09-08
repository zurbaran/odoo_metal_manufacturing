"""Tests del filtrado de planos según atributos y tipo de blueprint."""

import base64

from odoo.tests.common import TransactionCase


class TestBlueprintFiltering(TransactionCase):
    def setUp(self):
        super().setUp()

        Attribute = self.env["product.attribute"]
        AttributeValue = self.env["product.attribute.value"]

        self.attr_vidrio = Attribute.create({"name": "Vidrio"})
        self.val_transp = AttributeValue.create(
            {"name": "Transparente", "attribute_id": self.attr_vidrio.id}
        )
        self.val_carglas = AttributeValue.create(
            {"name": "Impreso Carglas", "attribute_id": self.attr_vidrio.id}
        )

        self.attr_acabado = Attribute.create({"name": "Acabado"})
        self.val_pulido = AttributeValue.create(
            {"name": "Pulido", "attribute_id": self.attr_acabado.id}
        )
        self.val_mate = AttributeValue.create(
            {"name": "Mate", "attribute_id": self.attr_acabado.id}
        )

        self.product_template = self.env["product.template"].create(
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
                            "value_ids": [(6, 0, [self.val_pulido.id, self.val_mate.id])],
                        },
                    ),
                ],
            }
        )

        self.product_transp_pulido = self._variant_for(
            self.val_transp, self.val_pulido
        )
        self.product_transp_mate = self._variant_for(self.val_transp, self.val_mate)
        self.product_carglas_pulido = self._variant_for(
            self.val_carglas, self.val_pulido
        )

        self.blueprint = self._create_blueprint(
            "Plano Transparente",
            "purchase",
            [(self.attr_vidrio, [self.val_transp])],
        )

    def _variant_for(self, *values):
        expected_ids = {value.id for value in values}
        variant = self.product_template.product_variant_ids.filtered(
            lambda product: set(
                product.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id"
                ).ids
            )
            == expected_ids
        )[:1]
        self.assertTrue(variant, "No se encontró la variante esperada para el test")
        return variant

    def _create_blueprint(self, name, type_blueprint, conditions):
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'width="10" height="10"></svg>'
        )
        return self.env["product.blueprint"].create(
            {
                "name": name,
                "product_id": self.product_template.id,
                "type_blueprint": type_blueprint,
                "file": base64.b64encode(svg),
                "blueprint_condition_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, [value.id for value in values])],
                        },
                    )
                    for attribute, values in conditions
                ],
            }
        )

    def _evaluated_names(self, product, type_blueprint):
        line = self.env["sale.order.line"].new({"product_id": product.id})
        return [
            item["blueprint_name"]
            for item in line._get_evaluated_blueprint(type_blueprint=type_blueprint)
        ]

    def test_blueprint_is_included_when_attribute_matches(self):
        names = self._evaluated_names(self.product_transp_pulido, "purchase")
        self.assertIn("Plano Transparente", names)

    def test_blueprint_is_excluded_when_attribute_does_not_match(self):
        names = self._evaluated_names(self.product_carglas_pulido, "purchase")
        self.assertNotIn("Plano Transparente", names)

    def test_blueprint_without_conditions_applies(self):
        blueprint = self._create_blueprint("Plano Libre", "purchase", [])
        names = self._evaluated_names(self.product_carglas_pulido, "purchase")
        self.assertIn(blueprint.name, names)

    def test_blueprint_with_multiple_conditions(self):
        blueprint = self._create_blueprint(
            "Plano Múltiple",
            "purchase",
            [
                (self.attr_vidrio, [self.val_transp]),
                (self.attr_acabado, [self.val_pulido]),
            ],
        )

        names_ok = self._evaluated_names(self.product_transp_pulido, "purchase")
        self.assertIn(blueprint.name, names_ok)

        names_fail = self._evaluated_names(self.product_transp_mate, "purchase")
        self.assertNotIn(blueprint.name, names_fail)

    def test_blueprint_with_multiple_attribute_conditions_must_all_match(self):
        blueprint = self._create_blueprint(
            "Plano MultiAtributo",
            "manufacturing",
            [
                (self.attr_vidrio, [self.val_transp]),
                (self.attr_acabado, [self.val_pulido]),
            ],
        )

        names_ok = self._evaluated_names(self.product_transp_pulido, "manufacturing")
        self.assertIn(blueprint.name, names_ok)

        names_fail = self._evaluated_names(self.product_transp_mate, "manufacturing")
        self.assertNotIn(blueprint.name, names_fail)
