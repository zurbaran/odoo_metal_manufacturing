from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Extensión del modelo sale.order para la impresión del reporte de blueprints."""

    _inherit = "sale.order"

    def action_print_blueprint(self):
        """
        Acción para imprimir el reporte de blueprints.
        Para usar en un botón.
        """
        self.ensure_one()
        _logger.info(
            f"[Blueprint] Imprimiendo blueprints de fabricación para el pedido: {self.name}"
        )

        return self.env.ref(
            "product_blueprint_manager.action_report_sale_order_blueprint"
        ).report_action(self)

    def action_print_purchase_blueprint(self):
        self.ensure_one()
        _logger.info(
            f"[Blueprint] Imprimiendo blueprints de compra para el pedido: {self.name}"
        )
        return self.env.ref(
            "product_blueprint_manager.action_report_purchase_order_blueprint"
        ).report_action(self)

    def _get_report_base_filename(self):
        """
        Sobreescribe el nombre base del reporte para el nuevo informe de blueprints.

        Returns:
            str: El nombre base del reporte.
        """
        self.ensure_one()
        if (
            self.env.context.get("active_model") == "sale.order"
            and self.env.context.get("active_id") == self.id
        ):
            report = self.env.context.get("report")
            if report == "product_blueprint_manager.report_sale_order_blueprint_document":
                return f"Plano_Fabricacion_{self.name}"
            elif report == "product_blueprint_manager.report_purchase_order_blueprint_document":
                return f"Plano_Compra_{self.name}"
        return super(SaleOrder, self)._get_report_base_filename()
