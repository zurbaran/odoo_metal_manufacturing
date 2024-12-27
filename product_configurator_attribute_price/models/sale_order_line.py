from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_custom_attribute_value_ids')
    def _compute_price_unit(self):
        """
        Calcula el precio unitario basado en los valores personalizados de los atributos.
        """
        for line in self:
            if not line.product_id:
                _logger.warning(f"[Line {line.id}] No product selected. Skipping price calculation.")
                continue

            if line.order_id.state in ['sale', 'done']:
                _logger.info(f"[Line {line.id}] Order state '{line.order_id.state}'. Skipping price update.")
                continue

            # Inicia con el precio base del producto
            price_so_far = line.product_id.lst_price
            _logger.info(f"[Line {line.id}] Base price for {line.product_id.name}: {price_so_far}")

            # Procesar cada atributo
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id

                if attribute_value:
                    try:
                        # **1. Procesar `custom_value` si está en la fórmula**
                        if 'custom_value' in (attribute_value.price_formula or ''):
                            increment = attribute_value.calculate_price_increment(
                                custom_value=custom_attribute.custom_value,
                                price_so_far=price_so_far
                            )
                            price_so_far += increment
                            _logger.info(f"[Line {line.id}] Increment from {attribute_value.name} (custom_value): {increment}")

                        # **2. Procesar `price_so_far` si está en la fórmula**
                        elif 'price_so_far' in (attribute_value.price_formula or ''):
                            increment = attribute_value.calculate_price_increment(
                                custom_value=0,  # No se usa custom_value aquí
                                price_so_far=price_so_far
                            )
                            price_so_far += increment
                            _logger.info(f"[Line {line.id}] Increment from {attribute_value.name} (price_so_far): {increment}")

                        # **3. Aplicar `price_extra` si está configurado**
                        elif attribute_value.price_extra > 0:
                            _logger.info(f"[Line {line.id}] Applying price_extra for {attribute_value.name}: {attribute_value.price_extra}")
                            price_so_far += attribute_value.price_extra

                    except Exception as e:
                        _logger.error(f"[Line {line.id}] Error processing attribute {attribute_value.name}: {e}")

            # Asignar el precio calculado al price_unit
            line.price_unit = price_so_far
            line.price_subtotal = line.price_unit * line.product_uom_qty
            _logger.info(f"[Line {line.id}] Final price_unit: {line.price_unit}, price_subtotal: {line.price_subtotal}")
