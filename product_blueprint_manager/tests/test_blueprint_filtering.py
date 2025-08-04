from odoo.tests.common import TransactionCase  # pyright: ignore[reportMissingImports]


class TestBlueprintFiltering(TransactionCase):
    def setUp(self):
        super().setUp()
        ProductTemplate = self.env["product.template"]
        Product = self.env["product.product"]  # noqa: F841
        Attribute = self.env["product.attribute"]
        AttributeValue = self.env["product.attribute.value"]
        Blueprint = self.env["product.blueprint"]

        # Crear atributo y valores
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

        # Crear producto con atributo
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
                    )
                ],
            }
        )
        self.product = self.product_template.product_variant_ids[0]

        # Crear blueprint con filtro: requiere "Transparente"
        self.blueprint = Blueprint.create(
            {
                "name": "Plano Transparente",
                "type": "purchase",
                "product_tmpl_id": self.product_template.id,
                "attribute_filter_id": self.attr_vidrio.id,
                "attribute_filter_value_ids": [(6, 0, [self.val_transp.id])],
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
        selected = [v.name for v in order_line.product_template_attribute_value_ids]
        required = [v.name for v in self.blueprint.attribute_filter_value_ids]
        self.assertTrue(
            all(val in selected for val in required), "El plano debería incluirse"
        )

    def test_blueprint_is_excluded_when_attribute_does_not_match(self):
        # Simula línea con valor "Impreso Carglas"
        order_line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_template_attribute_value_ids": [(6, 0, [self.val_carglas.id])],
            }
        )
        selected = [v.name for v in order_line.product_template_attribute_value_ids]
        required = [v.name for v in self.blueprint.attribute_filter_value_ids]
        self.assertFalse(
            all(val in selected for val in required), "El plano no debe incluirse"
        )
