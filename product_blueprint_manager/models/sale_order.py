from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_blueprint(self):
        """Acción para imprimir el reporte de blueprints."""
        self.ensure_one()
        _logger.info(f"[Blueprint] Imprimiendo blueprints para el pedido: {self.name}")

        return self.env.ref('product_blueprint_manager.action_report_sale_order_blueprint').report_action(self)

    def _get_report_base_filename(self):
        """Sobreescribe el nombre base del reporte para el nuevo informe de blueprints."""
        self.ensure_one()
        if self.env.context.get('active_model') == 'sale.order' and self.env.context.get('active_id') == self.id:
            report = self.env.context.get('report')
            if report == 'product_blueprint_manager.report_sale_order_blueprint_document':
                return f"Blueprints_{self.name}"
        return super(SaleOrder, self)._get_report_base_filename()

    def _get_sale_order_report_data(self, report_name):
        """Devuelve los datos necesarios para el reporte de blueprints."""
        data = {}
        if report_name == 'product_blueprint_manager.action_report_sale_order_blueprint':
            data['doc_ids'] = self.ids
            data['doc_model'] = 'sale.order'
            data['docs'] = self
        return data
