from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintFilters(TransactionCase):
    def test_blueprint_filtered_by_attribute(self):
        attr = self.env["product.attribute"].create({"name": "Vidrio"})
        val = self.env["product.attribute.value"].create(
            {"name": "Transparente", "attribute_id": attr.id}
        )
        tmpl = self.env["product.template"].create(
            {
                "name": "Producto con Filtro",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attr.id,
                            "value_ids": [(6, 0, [val.id])],
                        },
                    )
                ],
            }
        )
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano Solo Transparente",
                "product_tmpl_id": tmpl.id,
                "attribute_filter_id": attr.id,
                "attribute_filter_value_ids": [(6, 0, [val.id])],
                "svg_file": b"<svg></svg>",
                "type": "manufacturing",
            }
        )
        product = tmpl.product_variant_id
        line = self.env["sale.order.line"].new(  # noqa: F841
            {
                "product_id": product.id,
                "product_template_attribute_value_ids": [(6, 0, [val.id])],
            }
        )
        self.assertIn(val.name, [v.name for v in blueprint.attribute_filter_value_ids])
