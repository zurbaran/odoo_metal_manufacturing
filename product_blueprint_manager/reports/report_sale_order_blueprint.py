from odoo import models
import logging

_logger = logging.getLogger(__name__)

class ReportBlueprintAutoGenerate(models.AbstractModel):
    _name = "report.product_blueprint_manager.report_sale_order_blueprint"
    _description = "Generador automático de planos evaluados antes del reporte"

    def _get_report_values(self, docids, data=None):
        orders = self.env["sale.order"].browse(docids)
        for order in orders:
            _logger.info(f"[Blueprint][Auto] Procesando orden {order.name}")
            for line in order.order_line:
                _logger.info(f"[Blueprint][Auto] Línea {line.id} - Producto: {line.product_id.name}")
                line._get_evaluated_blueprint()
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': orders,
        }
