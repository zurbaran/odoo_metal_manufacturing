import logging

from odoo import api, fields, models  # pyright: ignore[reportMissingImports]
from odoo.tools.safe_eval import safe_eval  # pyright: ignore[reportMissingImports]

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_modified = fields.Monetary(
        string="Precio Modificado",
        currency_field="currency_id",
        compute="_compute_price_modified",
        store=False,
    )

    @api.depends("price_unit")
    def _compute_price_modified(self):
        for line in self:
            line.price_modified = line.price_unit

    @api.onchange(
        "product_id",
        "product_uom_qty",
        "product_uom",
        "order_id.partner_id",
        "order_id.pricelist_id",
        "product_custom_attribute_value_ids",
        "product_no_variant_attribute_value_ids",
    )
    def _onchange_product_id(self):
        # 1) Primero deja que Odoo calcule el precio base
        res = super()._onchange_product_id()

        # 2) Luego aplica tus fórmulas sobre ese base_price
        for line in self:
            if not line.product_id:
                continue

            price_so_far = line.price_unit
            _logger.debug(f"[Line {line.id}] Base Odoo: {price_so_far}")

            # A) Fórmulas que usan custom_value
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                formula = getattr(ptav, "price_formula", False)
                if not formula or "custom_value" not in formula:
                    continue
                try:
                    cv = float(cav.custom_value or 0.0)
                    incr = safe_eval(
                        formula,
                        {"__builtins__": {}},
                        {"custom_value": cv, "price_so_far": price_so_far},
                    )
                    incr = float(incr)
                except Exception as e:
                    _logger.exception(
                        "[Line %s] Error evaluando fórmula %r en %s: %s",
                        line.id,
                        formula,
                        ptav.display_name,
                        e,
                    )
                    incr = 0.0
                if incr < 0:
                    incr = 0.0
                price_so_far += incr
                _logger.debug(
                    "[Line %s] +%s por %s → %s",
                    line.id,
                    incr,
                    ptav.display_name,
                    price_so_far,
                )

            # B) Fórmulas que usan price_so_far
            for nav in line.product_no_variant_attribute_value_ids:
                formula = getattr(nav, "price_formula", False)
                if not formula or "price_so_far" not in formula:
                    continue
                try:
                    incr = safe_eval(
                        formula,
                        {"__builtins__": {}},
                        {"price_so_far": price_so_far},
                    )
                    incr = float(incr)
                except Exception as e:
                    _logger.exception(
                        "[Line %s] Error evaluando fórmula %r en %s: %s",
                        line.id,
                        formula,
                        nav.display_name,
                        e,
                    )
                    incr = 0.0
                if incr < 0:
                    incr = 0.0
                price_so_far += incr
                _logger.debug(
                    "[Line %s] +%s por %s → %s",
                    line.id,
                    incr,
                    nav.display_name,
                    price_so_far,
                )

            # C) price_extra al final
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                price_so_far += ptav.price_extra or 0.0
            for nav in line.product_no_variant_attribute_value_ids:
                price_so_far += nav.price_extra or 0.0

            # 3) Redondeo y asignación final
            final_price = line.currency_id.round(price_so_far)
            line.price_unit = final_price
            _logger.info("[Line %s] Precio final calculado: %s", line.id, final_price)

        return res
