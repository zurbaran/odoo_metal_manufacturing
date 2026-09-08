import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

_BLUEPRINT_USER_GROUP = "product_blueprint_manager.group_product_blueprint_user"


class ProductTemplate(models.Model):
    """Extensión de ``product.template`` para planos y fórmulas."""

    _inherit = "product.template"

    blueprint_ids = fields.One2many(
        "product.blueprint",
        "product_id",
        string="Planos",
        groups=_BLUEPRINT_USER_GROUP,
    )

    formula_ids = fields.One2many(
        "product.blueprint.formula",
        "product_id",
        string="Fórmulas",
        groups=_BLUEPRINT_USER_GROUP,
    )

    attribute_ids = fields.Many2many(
        comodel_name="product.attribute",
        compute="_compute_attribute_ids",
        store=False,
    )

    def _check_blueprint_user_access(self):
        """Require explicit blueprint access for public blueprint helpers."""
        if not self.env.user.has_group(_BLUEPRINT_USER_GROUP):
            raise AccessError(_("No tiene permisos para acceder a planos de producto."))

    def get_custom_attribute_values(self, sale_order_line=None):
        """Return the formula variables captured for a sale order line."""
        self._check_blueprint_user_access()
        _logger.debug(
            "[Blueprint] Obteniendo valores de atributos personalizados para %s, "
            "línea de venta: %s",
            self.name,
            sale_order_line.id if sale_order_line else "Ninguna",
        )
        return sale_order_line.blueprint_custom_values if sale_order_line else {}

    def generate_blueprint_report(self, sale_order_line=None):
        """Generate the blueprint report for the supplied sale order line."""
        self.ensure_one()
        self._check_blueprint_user_access()

        if not sale_order_line:
            _logger.error("Sale order line is required for generating the blueprint.")
            return False

        _logger.info(
            "Generando reporte de blueprint para el producto %s (SO line ID: %s)",
            self.name,
            sale_order_line.id,
        )

        report_action = self.env["ir.actions.report"]._get_report_from_name(
            "product_blueprint_manager.action_report_sale_order_blueprint"
        )
        return report_action.report_action(sale_order_line.order_id)

    @api.depends("attribute_line_ids")
    def _compute_attribute_ids(self):
        for product in self:
            product.attribute_ids = product.attribute_line_ids.mapped("attribute_id")
