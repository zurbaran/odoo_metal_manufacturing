from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

# Verificar si el modelo 'product.blueprint.attribute.hook' existe
if 'product.blueprint.attribute.hook' in models.Model._inherits:
    class ProductConfiguratorAttributeHook(models.AbstractModel):
        _inherit = 'product.blueprint.attribute.hook'

        def get_attribute_values_for_blueprint(self, sale_order_line):
            """
            Devuelve los valores de atributos específicos usados en el configurador de productos para un blueprint.
            """
            attribute_values = {}
            for custom_value in sale_order_line.product_custom_attribute_value_ids:
                attribute_id_name = custom_value.custom_product_template_attribute_value_id.name
                if attribute_id_name:
                    attribute_values[attribute_id_name] = custom_value.custom_value
            _logger.info(f"[Hook] Valores personalizados capturados: {attribute_values}")
            return attribute_values
else:
    class ProductConfiguratorAttributeHook(models.AbstractModel):
        _name = 'product.configurator.attribute.hook'
        _description = 'Devuelve los valores de atributos específicos usados en el configurador de productos para un blueprint.'

        def get_attribute_values_for_blueprint(self, sale_order_line):
            """
            Devuelve los valores de atributos específicos usados en el configurador de productos para un blueprint.
            """
            attribute_values = {}
            for custom_value in sale_order_line.product_custom_attribute_value_ids:
                attribute_id_name = custom_value.custom_product_template_attribute_value_id.name
                if attribute_id_name:
                    attribute_values[attribute_id_name] = custom_value.custom_value
            _logger.info(f"[Hook] Valores personalizados capturados: {attribute_values}")
            return attribute_values