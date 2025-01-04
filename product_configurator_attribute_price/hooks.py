from odoo import models

class ProductConfiguratorAttributeHook(models.AbstractModel):
    _inherit = 'product.blueprint.attribute.hook'

    def get_attribute_values_for_blueprint(self, sale_order_line):
        """
        Devuelve los valores de atributos específicos usados en el configurador de productos.
        """
        attribute_values = {}
        for attribute_value in sale_order_line.product_custom_attribute_value_ids:
            attribute_values[attribute_value.attribute_id.name] = attribute_value.name
        return attribute_values

