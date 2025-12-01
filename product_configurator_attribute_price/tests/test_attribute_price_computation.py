from odoo.tests.common import TransactionCase


class TestAttributePriceComputation(TransactionCase):
    """
    Suite de tests para verificar el cálculo del precio unitario en líneas de venta
    cuando intervienen:
      - Atributos personalizados (is_custom=True)
      - Fórmulas de precio (price_formula)
      - Incrementos fijos nativos (price_extra)
    """

    def setUp(self):
        """
        Prepara los datos de prueba básicos:
          - Crea un atributo 'Largo' marcado como is_custom=True y sin generación
            de variantes (create_variant='no_variant').
          - Crea un valor de atributo de plantilla (ptav) asociado a 'Largo',
            con una fórmula de precio y un price_extra fijo.
          - Crea un producto base con precio de venta y coste estándar.
        """
        super().setUp()

        # Atributo personalizado, sin generación de variantes
        self.attribute = self.env["product.attribute"].create(
            {"name": "Largo", "create_variant": "no_variant", "is_custom": True}
        )

        # Valor de atributo de plantilla con fórmula y extra:
        #   - price_formula: custom_value * 0.5
        #   - price_extra: 10
        # De esta forma, el incremento se compone de una parte variable
        # y una parte fija.
        self.ptav = self.env["product.template.attribute.value"].create(
            {
                "name": "Valor Largo",
                "attribute_id": self.attribute.id,
                "price_formula": "custom_value * 0.5",
                "price_extra": 10,
            }
        )

        # Producto base sobre el que se calculará el precio final.
        # list_price será la base de cálculo a la que se sumarán
        # los incrementos de los atributos.
        self.product = self.env["product.product"].create(
            {
                "name": "Producto Base",
                "type": "consu",
                "list_price": 100.0,
                "standard_price": 80.0,
            }
        )

    def test_price_computation_with_formula_and_price_extra(self):
        """
        Verifica que el cálculo del precio unitario de la línea de venta:
          - Parte del list_price del producto (100)
          - Aplica la fórmula del atributo: custom_value * 0.5  -> 200 * 0.5 = 100
          - Suma el price_extra definido en el ptav: 10
          - Resultado esperado: 100 (base) + 100 (fórmula) + 10 (extra) = 210

        El test comprueba que line.price_unit coincide con el valor esperado
        tras ejecutar el onchange de producto.
        """
        # Se crea una nueva línea de venta en memoria (new), sin grabarla en BD.
        # Se pasa:
        #   - product_id: producto base
        #   - product_uom_qty: cantidad (1.0)
        #   - product_custom_attribute_value_ids: un atributo personalizado 'Largo'
        #     con custom_value = 200, enlazado a self.ptav.
        line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "product_custom_attribute_value_ids": [
                    (
                        0,
                        0,
                        {
                            "custom_product_template_attribute_value_id": self.ptav.id,
                            "custom_value": 200,
                        },
                    )
                ],
            }
        )

        # Dispara la lógica de Odoo y del módulo asociado al onchange de product_id.
        # Aquí se recalcula line.price_unit aplicando la fórmula y el price_extra.
        line._onchange_product_id()

        # Cálculo manual del precio esperado para compararlo:
        #   100 (list_price) + (200 * 0.5) + 10  =  100 + 100 + 10 = 210
        expected_price = 100 + (200 * 0.5) + 10

        # Se comprueba que el precio unitario de la línea coincide con el esperado,
        # usando el redondeo de la moneda asociada a la línea.
        self.assertEqual(line.price_unit, line.currency_id.round(expected_price))
