from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    blueprint_ids = fields.One2many('product.blueprint', 'product_id', string='Blueprints')
    formula_ids = fields.One2many('product.blueprint.formula', 'product_id', string='Fórmulas')

    def get_custom_attribute_values(self, sale_order_line=None):
        """Get custom attribute values for a given sale order line.
        
        Args:
            sale_order_line (recordset): The sale order line record.

        Returns:
            dict: A dictionary of custom attribute values.
        """
        _logger.info(f"[Blueprint] Obteniendo valores de atributos personalizados para {self.name}, Linea de venta: {sale_order_line.id if sale_order_line else 'Ninguna'}")
        return sale_order_line.blueprint_custom_values if sale_order_line else {}

    def generate_blueprint_report(self, sale_order_line=None, mode='preview'):
        """Genera un reporte de blueprint."""
        self.ensure_one()
        blueprint = self.blueprint_ids[:1]
        if not blueprint or not blueprint.file:
            _logger.warning(f"[Blueprint] No hay blueprint para el producto: {self.name}")
            return False

        if sale_order_line:
            variables = self.get_custom_attribute_values(sale_order_line)
        else:
            variables = None

        blueprint_svg = self.env['sale.order.line']._generate_evaluated_blueprint_svg(blueprint, mode, variables)

        if blueprint_svg:
            report_template = 'product_blueprint_manager.report_blueprint_template' if mode == 'preview' else 'product_blueprint_manager.report_final_blueprint'
            report_action = self.env['ir.actions.report']._get_report_from_name(report_template)
            blueprint_svg_b64 = blueprint_svg
            return report_action.report_action(self, data={'blueprint_svg': blueprint_svg_b64, 'mode': mode})
        return False
