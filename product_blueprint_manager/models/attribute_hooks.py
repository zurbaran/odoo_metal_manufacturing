from odoo import models
import logging

_logger = logging.getLogger(__name__)

class ProductBlueprintAttributeHook(models.AbstractModel):
    _inherit = 'product.configurator.attribute.hook'
    _name = 'product.blueprint.attribute.hook'
    _description = 'Hook for Attribute Value Retrieval'

    def get_attribute_values_for_blueprint(self, sale_order_line):
        """Retrieve attribute values for a given sale order line.

        Args:
            sale_order_line (recordset): The sale order line record.

        Returns:
            dict: A dictionary of attribute values.
        """
        _logger.info(f"[Blueprint] Llamando al super get_attribute_values_for_blueprint para la línea {sale_order_line.id if sale_order_line else 'Ninguna'}")
        return super().get_attribute_values_for_blueprint(sale_order_line)
