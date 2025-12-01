from odoo.tests.common import TransactionCase


class TestDescriptionGeneration(TransactionCase):
    """
    Conjunto de tests funcionales relacionados con la generación de la descripción
    de la línea de venta (`sale.order.line.name`) cuando intervienen atributos
    personalizados (is_custom / product_custom_attribute_value_ids).
    """

    def setUp(self):
        """
        Prepara los datos mínimos para las pruebas:

        - Crea un atributo "Alto" marcado como:
          * create_variant = "no_variant": no genera variantes de producto.
          * is_custom = True: permite introducir un valor numérico personalizado.
        - Crea un valor de atributo de plantilla (PTAV) llamado "mmA" asociado al
          atributo "Alto".
        - Crea un producto simple "Mampara Base" sobre el que se probará
          la generación de la descripción.
        """
        super().setUp()

        # Atributo personalizado de tipo numérico (is_custom=True)
        #  que no genera variantes
        self.attribute = self.env["product.attribute"].create(
            {"name": "Alto", "create_variant": "no_variant", "is_custom": True}
        )

        # Valor de atributo de plantilla (PTAV) asociado al atributo "Alto"
        # Este PTAV será el que se relacione con el valor personalizado (custom_value)
        self.ptav = self.env["product.template.attribute.value"].create(
            {
                "name": "mmA",
                "attribute_id": self.attribute.id,
            }
        )

        # Producto base sobre el que se configurará la línea de venta
        self.product = self.env["product.product"].create({"name": "Mampara Base"})

    def test_description_contains_custom_attribute(self):
        """
        Verifica que la descripción de la línea de venta (`line.name`) contenga:

            "Alto: mmA: 1456.0"

        Es decir:
        - El nombre del atributo (`Alto`).
        - El nombre del valor de atributo de plantilla (`mmA`).
        - El valor personalizado introducido (`1456.0`).

        Flujo del test:
        1. Crea una línea de pedido de venta en memoria (`new`) con:
           - product_id = Mampara Base
           - product_custom_attribute_value_ids con:
             * custom_product_template_attribute_value_id = PTAV "mmA"
             * custom_value = 1456
        2. Llama a `_onchange_product_id()`, que debe encargarse de:
           - Calcular precios.
           - Construir la descripción completa de la línea.
        3. Comprueba que la cadena esperada está incluida en `line.name`.
        """
        # Creamos una línea de venta en memoria (no grabada en BD)
        line = self.env["sale.order.line"].new(
            {
                "product_id": self.product.id,
                "product_custom_attribute_value_ids": [
                    (
                        0,
                        0,
                        {
                            # Referencia al PTAV "mmA" asociado al atributo "Alto"
                            "custom_product_template_attribute_value_id": self.ptav.id,
                            # Valor numérico introducido por el usuario
                            "custom_value": 1456,
                        },
                    )
                ],
            }
        )

        # Dispara la lógica de onchange para que se genere la descripción y el precio
        line._onchange_product_id()

        # Comprobamos que la descripción resultante contiene el texto esperado
        # Formato esperado: "<Nombre atributo>: <Nombre PTAV>: <custom_value>"
        self.assertIn("Alto: mmA: 1456.0", line.name)
