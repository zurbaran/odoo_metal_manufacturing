from odoo.tests.common import TransactionCase, tagged

# TransactionCase: caso de prueba que usa transacciones para aislar datos.
# tagged: permite etiquetar el test para ejecutarlo en determinados momentos
# (en este caso, NO en la instalación, pero SÍ en post_install).


@tagged("-at_install", "post_install")
class TestBlueprintFilters(TransactionCase):
    """Tests funcionales para comprobar el filtrado de planos (product.blueprint)
    en función de los atributos y valores seleccionados en un producto/línea de venta.

    Este test verifica que:
    - Un plano asociado a un producto con una condición de atributo/valor
      solo se aplique cuando la variante del producto cumple dicha condición.
    """

    def test_blueprint_filtered_by_attribute(self):
        """Comprueba que un plano se incluye cuando la línea de venta
        tiene el valor de atributo requerido por la condición del plano.
        """
        # 1) Crear atributo "Vidrio"
        attr = self.env["product.attribute"].create({"name": "Vidrio"})

        # 2) Crear valor de atributo "Transparente" asociado al atributo "Vidrio"
        val = self.env["product.attribute.value"].create(
            {"name": "Transparente", "attribute_id": attr.id}
        )

        # 3) Crear plantilla de producto con una línea de atributo "Vidrio"
        #    que permite el valor "Transparente"
        tmpl = self.env["product.template"].create(
            {
                "name": "Producto con Filtro",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            # Atributo al que pertenece la línea
                            "attribute_id": attr.id,
                            # value_ids se establece con el comando (6, 0, [ids])
                            # que en Odoo indica: "sustituye por exactamente estos IDs"
                            "value_ids": [(6, 0, [val.id])],
                        },
                    )
                ],
            }
        )

        # 4) Crear plano asociado a la plantilla de producto anterior,
        #    con una condición que exige el atributo "Vidrio" = "Transparente"
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Plano Solo Transparente",
                # Se vincula al product.template (no a la variante concreta)
                "product_tmpl_id": tmpl.id,
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
                # Contenido mínimo de un SVG para que el campo no esté vacío
                "svg_file": b"<svg></svg>",
                # Tipo de plano: fabricación (manufacturing)
                "type": "manufacturing",
            }
        )

        # 5) Obtener la variante de producto correspondiente a la plantilla
        #    (como solo hay un valor de atributo, habrá una sola variante)
        product = tmpl.product_variant_id

        # 6) Simular una línea de pedido de venta con:
        #    - product_id = variante anterior
        #    - product_template_attribute_value_ids = valor "Transparente"
        # Se usa new() para crear un registro en memoria (no guardado en BD)
        line = self.env["sale.order.line"].new(
            {
                "product_id": product.id,
                # Se indican los ptav (product.template.attribute.value) que
                # representan el valor seleccionado del atributo en esta línea.
                "product_template_attribute_value_ids": [(6, 0, [val.id])],
            }
        )

        # 7) Obtener los planos evaluados para esta línea. Internamente:
        #    - Filtra planos por producto/tipo.
        #    - Aplica las condiciones de atributos configuradas.
        evaluated = line._get_evaluated_blueprint()

        # 8) Extraer los nombres de plano devueltos para verificar
        #    que el plano "Plano Solo Transparente" se incluye en la lista.
        names = [b["blueprint_name"] for b in evaluated]

        # 9) Asegurarse de que el plano creado se ha aplicado correctamente.
        self.assertIn(blueprint.name, names, "El plano debería incluirse")
