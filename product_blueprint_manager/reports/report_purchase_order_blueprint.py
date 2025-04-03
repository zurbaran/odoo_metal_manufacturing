from odoo import models
import logging

_logger = logging.getLogger(__name__)

class ReportPurchaseOrderBlueprint(models.AbstractModel):
    _name = "report.product_blueprint_manager.report_purchase_order_blueprint"
    _description = "Generador de planos para orden de compra"

    def _get_report_values(self, docids, data=None):
        orders = self.env["sale.order"].browse(docids)
        for order in orders:
            _logger.info(f"[Blueprint][Purchase] Procesando orden {order.name}")
            for line in order.order_line:
                _logger.info(f"[Blueprint][Purchase] Línea {line.id} - Producto: {line.product_id.name}")
                line._get_evaluated_blueprint(type_blueprint='purchase')
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': orders,
        }

