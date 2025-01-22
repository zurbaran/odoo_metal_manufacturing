from odoo import models
import logging

_logger = logging.getLogger(__name__)


class ProductBlueprintHook(models.AbstractModel):
    """Hook para la recuperación de valores de atributos para el blueprint."""

    _inherit = "product.configurator.attribute.hook"
    _name = "product.blueprint.hook"
    _description = "Hook for Attribute Value Retrieval"

    def get_attribute_values_for_blueprint(self, sale_order_line):
        """
        Recupera los valores de atributos para una línea de pedido de venta dada.

        Args:
            sale_order_line (recordset): La línea de pedido de venta.

        Returns:
            dict: Un diccionario de valores de atributos.
        """
        _logger.info(
            f"[Blueprint] Llamando al super get_attribute_values_for_blueprint para la línea {sale_order_line.id if sale_order_line else 'Ninguna'}"
        )
        return super().get_attribute_values_for_blueprint(sale_order_line)