# Modelo auxiliar para almacenar valores personalizados
#  de atributos en las líneas de venta.
# Se utiliza principalmente cuando un atributo está marcado como "is_custom"
# y el usuario introduce un valor numérico (por ejemplo, medidas en mm)
#  en el configurador
# o en la cuadrícula de variantes. Estos valores se usan para:
#   - Cálculo dinámico de precio (vía fórmulas en product.template.attribute.value)
#   - Generación de descripciones detalladas en la línea de pedido
#   - Transmisión de información a otros módulos (planos, fabricación, etc.)

from odoo import fields, models


class ProductCustomAttributeValue(models.Model):
    """Valor personalizado para atributos en líneas de pedido de venta.

    Este modelo NO forma parte del estándar de Odoo, es un modelo propio
    que actúa como puente entre:

      * La línea de venta (sale.order.line)
      * El valor de atributo de plantilla (product.template.attribute.value)
      * El valor numérico introducido por el usuario (custom_value)

    Casos de uso típicos:
      - Atributos de tipo medida (mmA, mmB, Alto, Ancho, etc.)
      - Cálculo de recargos de precio en función de una fórmula que usa
        `custom_value` (definida en `price_formula` del PTAV)
      - Construcción de descripciones legibles en la línea de venta
    """

    _name = "product.custom.attribute.value"
    _description = "Valor personalizado para atributos en líneas de pedido"

    # Línea de venta a la que pertenece este valor personalizado.
    # ondelete="cascade" -> Si se elimina la línea de venta, se eliminan también
    # todos sus valores personalizados asociados.
    sale_order_line_id = fields.Many2one(
        "sale.order.line", string="Línea de venta", required=True, ondelete="cascade"
    )

    # Referencia al valor de atributo de plantilla (PTAV) que define:
    #   - El atributo (product.attribute) al que pertenece (ej. "Alto", "mmA")
    #   - Posibles metadatos como price_extra o price_formula
    # Esto permite relacionar el valor numérico con su contexto funcional
    # dentro del configurador y de las fórmulas de precio.
    custom_product_template_attribute_value_id = fields.Many2one(
        "product.template.attribute.value",
        string="Valor de atributo plantilla",
        required=True,
    )

    # Valor numérico introducido por el usuario para este PTAV.
    # Normalmente representa una medida (mm, cm, etc.) u otra magnitud
    # que se usará en:
    #   - Cálculos de precio (variables `custom_value` en price_formula)
    #   - Descripciones de la línea (ej.: "Alto: mmA: 1456.0")
    custom_value = fields.Float(string="Valor personalizado", required=True)
