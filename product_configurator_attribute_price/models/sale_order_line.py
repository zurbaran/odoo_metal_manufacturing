from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_custom_attribute_value_ids')
    def _compute_price_unit(self):
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                continue  # No modificar el precio si el pedido está bloqueado

            base_price = line.product_id.lst_price  # Precio base del producto
            final_price = base_price

            # Itera sobre atributos personalizados seleccionados
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id
                if attribute_value and attribute_value.price_formula:
                    # Calcula el incremento basado en la fórmula
                    increment = attribute_value.calculate_price_increment(custom_attribute.custom_value)
                    final_price += increment

            line.price_unit = final_price  # Actualizar price_unit
            line.price_subtotal = line.price_unit * line.product_uom_qty  # Actualizar price_subtotal también
