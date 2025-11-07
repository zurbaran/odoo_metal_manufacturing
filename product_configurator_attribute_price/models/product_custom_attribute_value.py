from odoo import fields, models


class ProductCustomAttributeValue(models.Model):
    _name = "product.custom.attribute.value"
    _description = "Valor personalizado para atributos en líneas de pedido"

    sale_order_line_id = fields.Many2one(
        "sale.order.line", string="Línea de venta", required=True, ondelete="cascade"
    )
    custom_product_template_attribute_value_id = fields.Many2one(
        "product.template.attribute.value",
        string="Valor de atributo plantilla",
        required=True,
    )
    custom_value = fields.Float(string="Valor personalizado", required=True)
