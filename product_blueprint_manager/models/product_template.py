from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """Extensión del modelo product.template para agregar la gestión de planos y fórmulas."""

    _inherit = "product.template"

    blueprint_ids = fields.One2many(
        "product.blueprint", "product_id", string="Planos"
    )
    formula_ids = fields.One2many(
        "product.blueprint.formula", "product_id", string="Fórmulas"
    )

    def get_custom_attribute_values(self, sale_order_line=None):
        """
        Obtiene los valores de atributos personalizados para una línea de pedido de venta dada.

        Args:
            sale_order_line (recordset): La línea de pedido de venta.

        Returns:
            dict: Un diccionario de valores de atributos personalizados.
        """
        _logger.info(
            f"[Blueprint] Obteniendo valores de atributos personalizados para {self.name}, Linea de venta: {sale_order_line.id if sale_order_line else 'Ninguna'}"
        )
        return sale_order_line.blueprint_custom_values if sale_order_line else {}

    def action_generate_blueprint_preview(self):
        """
        Genera una previsualización del primer plano asociado al producto.
        Acción para usar en un botón.
        """
        return self.generate_blueprint_report(mode="preview")

    def generate_blueprint_report(self, sale_order_line=None, mode="preview"):
        """
        Genera un reporte de blueprint.

        Args:
            sale_order_line (recordset, optional): La línea de pedido de venta para el reporte final. Defaults to None.
            mode (str, optional): El modo de generación del reporte ('preview' o 'final'). Defaults to 'preview'.

        Returns:
            dict or bool: La acción del reporte o False si hay un error.
        """
        self.ensure_one()
        if mode == "preview":
            blueprint = self.blueprint_ids[:1]
            if not blueprint or not blueprint.file:
                _logger.warning(
                    f"[Blueprint] No hay blueprint para el producto: {self.name}"
                )
                return False

            blueprint_svg = self.env["sale.order.line"]._generate_evaluated_blueprint_svg(
                blueprint, mode, variables=None
            )

            if blueprint_svg:
                report_action = self.env["ir.actions.report"]._get_report_from_name(
                    "product_blueprint_manager.report_blueprint_template"
                )
                blueprint_svg_b64 = blueprint_svg
                return report_action.report_action(
                    self, data={"blueprint_svg": blueprint_svg_b64, "mode": mode}
                )
            return False
        elif mode == "final":
            if not sale_order_line:
                _logger.error("Sale order line is required for 'final' mode.")
                return False

            report_action = self.env["ir.actions.report"]._get_report_from_name(
                "product_blueprint_manager.action_report_sale_order_blueprint"
            )
            return report_action.report_action(sale_order_line.order_id)
        else:
            _logger.warning(f"Unknown mode: {mode}")
            return False
