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
        """Extend the native Odoo 19 price compute with formula increments.

        Odoo 19 already includes native variant and no-variant ``price_extra``
        values in its base price. We therefore add only formula increments and
        custom-value extras that are not already part of the native combination.
        ``technical_price_unit`` is kept aligned with the computed result so
        Odoo can still distinguish computed prices from manual overrides.
        """
        super()._compute_price_unit()

        force_recompute = self.env.context.get("force_price_recomputation")
        for line in self:
            if (
                not line.order_id
                or not line.product_id
                or not line.product_uom_id
                or line.is_downpayment
                or line._is_global_discount()
                or line.qty_invoiced > 0
                or (line.product_id.expense_policy == "cost" and line.is_expense)
            ):
                continue

            currency = line.currency_id or line.company_id.currency_id or line.env.company.currency_id
            if (
                not force_recompute
                and currency.compare_amounts(line.technical_price_unit, line.price_unit)
            ):
                # Preserve a price that the user explicitly edited.
                continue

            price_so_far = line.price_unit
            custom_ptavs = line.product_custom_attribute_value_ids.mapped(
                "custom_product_template_attribute_value_id"
            )
            native_ptavs = (
                line.product_template_attribute_value_ids
                | line.product_no_variant_attribute_value_ids
            )

            # Custom values can use both custom_value and price_so_far.
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

                # The native price context does not necessarily contain custom
                # PTAVs. Add their fixed extra only when it was not already
                # included as a variant/no-variant value by Odoo.
                if ptav not in native_ptavs:
                    price_so_far += ptav.price_extra or 0.0

            # Apply price_so_far formulas for non-custom no-variant values.
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

            # Apply price_so_far formulas for variant values. Their native
            # price_extra has already been included by Odoo.
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
