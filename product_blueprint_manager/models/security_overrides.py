import logging

from odoo import _, models
from odoo.exceptions import AccessError

from ..utils import evaluate_math_expression

_logger = logging.getLogger(__name__)

_BLUEPRINT_USER_GROUP = "product_blueprint_manager.group_product_blueprint_user"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _check_blueprint_user_access(self):
        if not self.env.user.has_group(_BLUEPRINT_USER_GROUP):
            raise AccessError(_("No tiene permisos para generar planos de producto."))

    def action_print_blueprint(self):
        self._check_blueprint_user_access()
        return super().action_print_blueprint()

    def action_print_purchase_blueprint(self):
        self._check_blueprint_user_access()
        return super().action_print_purchase_blueprint()


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_print_blueprint_mrp(self):
        if not self.env.user.has_group(_BLUEPRINT_USER_GROUP):
            raise AccessError(_("No tiene permisos para generar planos de producto."))
        return super().action_print_blueprint_mrp()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def safe_evaluate_formula(self, expression, variables):
        """Evaluate blueprint formulas without executing arbitrary Python."""
        try:
            result = evaluate_math_expression(expression, variables)
            return str(result)
        except Exception as exc:
            _logger.warning(
                "[Blueprint] Fórmula rechazada por el evaluador seguro %r: %s",
                expression,
                exc,
            )
            return "Error"
