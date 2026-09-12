import logging

from odoo import api, fields, models

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

    @api.depends(
        "product_id",
        "product_uom_id",
        "product_uom_qty",
        "product_custom_attribute_value_ids.custom_product_template_attribute_value_id",
        "product_custom_attribute_value_ids.custom_value",
        "product_no_variant_attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _compute_price_unit(self):
        """Recompute on attribute changes while preserving Odoo 19 semantics.

        The native method decides whether a price is still computed or has been
        manually overridden. Formula application lives in ``_reset_price_unit``
        so manual prices remain untouched.
        """
        super()._compute_price_unit()

    def _reset_price_unit(self):
        """Extend Odoo 19's native price reset with attribute formulas.

        Odoo first computes its regular price, including native variant and
        no-variant ``price_extra`` values. We then add formula increments and
        custom-value extras not already contained in that native combination,
        finally keeping ``price_unit`` and ``technical_price_unit`` aligned.
        """
        self.ensure_one()
        super()._reset_price_unit()

        line = self
        if not line.product_id or not line.product_uom_id:
            return

        currency = (
            line.currency_id
            or line.company_id.currency_id
            or line.env.company.currency_id
        )
        price_so_far = line.price_unit
        custom_ptavs = line.product_custom_attribute_value_ids.mapped(
            "custom_product_template_attribute_value_id"
        )
        native_ptavs = (
            line.product_template_attribute_value_ids
            | line.product_no_variant_attribute_value_ids
        )

        for custom_value in line.product_custom_attribute_value_ids:
            ptav = custom_value.custom_product_template_attribute_value_id
            if not ptav:
                continue
            formula = ptav.price_formula
            if formula:
                try:
                    increment = ptav.calculate_price_increment(
                        float(custom_value.custom_value or 0.0),
                        price_so_far,
                    )
                except Exception as exc:
                    _logger.warning(
                        "[Line %s] Formula %r rejected for %s: %s",
                        line.id,
                        formula,
                        ptav.display_name,
                        exc,
                    )
                    increment = 0.0
                price_so_far += increment

            # Odoo's base combination already contains variant/no-variant
            # extras. A purely custom PTAV may not be present there.
            if ptav not in native_ptavs:
                price_so_far += ptav.price_extra or 0.0

        for ptav in line.product_no_variant_attribute_value_ids - custom_ptavs:
            formula = ptav.price_formula
            if formula and "price_so_far" in formula:
                try:
                    price_so_far += ptav.calculate_price_increment(0.0, price_so_far)
                except Exception as exc:
                    _logger.warning(
                        "[Line %s] Formula %r rejected for %s: %s",
                        line.id,
                        formula,
                        ptav.display_name,
                        exc,
                    )

        for ptav in line.product_template_attribute_value_ids - custom_ptavs:
            formula = ptav.price_formula
            if formula and "price_so_far" in formula:
                try:
                    price_so_far += ptav.calculate_price_increment(0.0, price_so_far)
                except Exception as exc:
                    _logger.warning(
                        "[Line %s] Formula %r rejected for %s: %s",
                        line.id,
                        formula,
                        ptav.display_name,
                        exc,
                    )

        final_price = currency.round(price_so_far)
        line.update(
            {
                "price_unit": final_price,
                "technical_price_unit": final_price,
            }
        )
        _logger.info("[Line %s] Precio final calculado: %s", line.id, final_price)

    @api.depends(
        "product_id",
        "linked_line_id",
        "linked_line_ids",
        "product_custom_attribute_value_ids.custom_product_template_attribute_value_id",
        "product_custom_attribute_value_ids.custom_value",
        "product_no_variant_attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _compute_name(self):
        """Keep the module's detailed attribute description on Odoo 19."""
        super()._compute_name()

        for line in self:
            if not line.product_id or line.is_downpayment:
                continue

            custom_ptav_ids = {
                cav.custom_product_template_attribute_value_id._origin.id
                for cav in line.product_custom_attribute_value_ids
                if cav.custom_product_template_attribute_value_id
            }
            descriptions = []

            for ptav in line.product_template_attribute_value_ids:
                if ptav.attribute_id and ptav.name:
                    descriptions.append(f"{ptav.attribute_id.name}: {ptav.name}")

            for ptav in line.product_no_variant_attribute_value_ids:
                if ptav._origin.id in custom_ptav_ids:
                    continue
                if ptav.attribute_id and ptav.name:
                    descriptions.append(f"{ptav.attribute_id.name}: {ptav.name}")

            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                if ptav and ptav.attribute_id:
                    descriptions.append(
                        f"{ptav.attribute_id.name}: {ptav.name}: {cav.custom_value}"
                    )

            line.name = line.product_id.display_name
            if descriptions:
                line.name += "\n" + "\n".join(descriptions)
