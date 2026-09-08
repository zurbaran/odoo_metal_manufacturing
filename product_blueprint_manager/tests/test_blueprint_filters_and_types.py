import base64

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintFilters(TransactionCase):
    """Comprueba el filtrado de planos por atributos del producto."""

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

        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'width="10" height="10"></svg>'
        )
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano Solo Transparente",
                "product_id": tmpl.id,
                "blueprint_condition_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attr.id,
                            "value_ids": [(6, 0, [val.id])],
                        },
                    )
                ],
                "file": base64.b64encode(svg),
                "type_blueprint": "manufacturing",
            }
        )

        product = tmpl.product_variant_id
        line = self.env["sale.order.line"].new({"product_id": product.id})
        evaluated = line._get_evaluated_blueprint()
        names = [item["blueprint_name"] for item in evaluated]

        self.assertIn(blueprint.name, names, "El plano debería incluirse")
