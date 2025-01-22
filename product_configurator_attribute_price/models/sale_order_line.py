from odoo import models, api, fields
import math
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """
    Hereda de sale.order.line para modificar el cálculo del precio unitario
    considerando las fórmulas de los atributos.
    """
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_custom_attribute_value_ids', 'product_no_variant_attribute_value_ids')
    def _compute_price_unit(self):
        """
        Calcula el precio unitario, aplicando fórmulas y ajustes específicos
        para atributos configurables.
        """
        for line in self:
            if not line.product_id:
                _logger.warning(f"[Line {line.id}] Producto no definido. Saltando cálculo.")
                continue

            # Precio inicial basado en el precio del producto
            price_so_far = line.product_id.lst_price
            _logger.info(f"[Line {line.id}] Precio inicial: {price_so_far}")

            # Procesar atributos de tipo "medida" (custom_value)
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id

                if attribute_value and attribute_value.price_formula and 'custom_value' in attribute_value.price_formula:
                    try:
                        custom_value = float(custom_attribute.custom_value or 0)
                        # Evaluar la formula de manera segura:
                        increment = eval(
                            attribute_value.price_formula,
                            {"__builtins__": None},  # Evitar el uso de funciones incorporadas peligrosas
                            {"custom_value": custom_value, "price_so_far": price_so_far, "math": math}
                        )

                        if increment < 0:
                            increment = 0
                        price_so_far += increment
                        _logger.info(f"[Line {line.id}] Incremento por custom_value ({attribute_value.name}): {increment}")
                    except Exception as e:
                        _logger.error(f"[Line {line.id}] Error al evaluar la fórmula para {attribute_value.name}: {e}")
                        continue

            # Procesar atributos de tipo "price_so_far"
            for no_variant_attribute in line.product_no_variant_attribute_value_ids:
                if no_variant_attribute and no_variant_attribute.price_formula and 'price_so_far' in no_variant_attribute.price_formula:
                    try:
                        increment = eval(
                            no_variant_attribute.price_formula,
                            {"__builtins__": None},
                            {"price_so_far": price_so_far, "math": math}
                        )
                        if increment < 0:
                            increment = 0
                        price_so_far += increment
                        _logger.info(f"[Line {line.id}] Incremento por price_so_far ({no_variant_attribute.name}): {increment}")
                    except Exception as e:
                        _logger.error(f"[Line {line.id}] Error al evaluar la fórmula para {no_variant_attribute.name}: {e}")
                        continue

            # Aplicar price_extra después de procesar las fórmulas
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id
                if attribute_value and attribute_value.price_extra:
                    price_so_far += attribute_value.price_extra
                    _logger.info(f"[Line {line.id}] Incremento por price_extra ({attribute_value.name}): {attribute_value.price_extra}")

            for no_variant_attribute in line.product_no_variant_attribute_value_ids:
                if no_variant_attribute and no_variant_attribute.price_extra:
                    price_so_far += no_variant_attribute.price_extra
                    _logger.info(f"[Line {line.id}] Incremento por price_extra ({no_variant_attribute.name}): {no_variant_attribute.price_extra}")

            # Asignar precio final al campo price_unit
            line.price_unit = price_so_far
            _logger.info(f"[Line {line.id}] Precio final calculado: {line.price_unit}")
