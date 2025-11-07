import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_custom_attribute_value_ids = fields.One2many(
        "product.custom.attribute.value",
        "sale_order_line_id",
        string="Valores personalizados de atributos",
    )

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
        "order_id",
        "product_custom_attribute_value_ids",
        "product_no_variant_attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _onchange_product_id(self):
        res = super()._onchange_product_id()

        for line in self:
            if not line.product_id:
                continue

            price_so_far = line.price_unit
            _logger.debug(f"[Line {line.id}] Base Odoo: {price_so_far}")

            # A) Fórmulas con custom_value
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                if not ptav:
                    continue

                formula = getattr(ptav, "price_formula", False)
                if not formula or "custom_value" not in formula:
                    continue
                try:
                    cv = float(cav.custom_value or 0.0)
                    incr = ptav.calculate_price_increment(cv, price_so_far)
                except Exception as e:
                    _logger.exception(
                        "[Line %s] Error evaluando fórmula %r en %s: %s",
                        line.id,
                        formula,
                        ptav.display_name,
                        e,
                    )
                    incr = 0.0

                price_so_far += incr

            # B) Fórmulas con price_so_far
            for nav in line.product_no_variant_attribute_value_ids:
                formula = getattr(nav, "price_formula", False)
                if formula and "price_so_far" in formula:
                    try:
                        incr = nav.calculate_price_increment(0.0, price_so_far)
                    except Exception as e:
                        _logger.exception(
                            "[Line %s] Error fórmula %r en %s: %s",
                            line.id,
                            formula,
                            nav.display_name,
                            e,
                        )
                        incr = 0.0
                    price_so_far += incr

            for ptav in line.product_template_attribute_value_ids:
                formula = getattr(ptav, "price_formula", False)
                if formula and "price_so_far" in formula:
                    try:
                        incr = ptav.calculate_price_increment(0.0, price_so_far)
                    except Exception as e:
                        _logger.exception(
                            "[Line %s] Error fórmula %r en %s: %s",
                            line.id,
                            formula,
                            ptav.display_name,
                            e,
                        )
                        incr = 0.0
                    price_so_far += incr

            # C) Sumar price_extra
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                price_so_far += ptav.price_extra or 0.0
            for nav in line.product_no_variant_attribute_value_ids:
                price_so_far += nav.price_extra or 0.0
            for ptav in line.product_template_attribute_value_ids:
                price_so_far += ptav.price_extra or 0.0

            final_price = line.currency_id.round(price_so_far)
            line.price_unit = final_price
            _logger.info("[Line %s] Precio final calculado: %s", line.id, final_price)

            # ----------------------------
            # Construcción de descripción
            # ----------------------------
            _logger.debug("[Line %s] === INICIO descripción personalizada ===", line.id)

            # Dump de los atributos custom
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                _logger.debug(
                    "[Line %s] CUSTOM -> Atributo: %s, PTAV: %s (%s), Valor: %s",
                    line.id,
                    ptav.attribute_id.name if ptav and ptav.attribute_id else "N/A",
                    ptav.name if ptav else "N/A",
                    ptav.id if ptav else "N/A",
                    cav.custom_value,
                )

            # Dump de los atributos no_variant
            for nav in line.product_no_variant_attribute_value_ids:
                _logger.debug(
                    "[Line %s] NO_VARIANT -> Atributo: %s, PTAV: %s (%s)",
                    line.id,
                    nav.attribute_id.name if nav.attribute_id else "N/A",
                    nav.name,
                    nav.id,
                )

            descriptions = []

            # Recolectamos los ptav de atributos custom (referencia directa)

            custom_ptav_ids = {
                cav.custom_product_template_attribute_value_id._origin.id
                for cav in line.product_custom_attribute_value_ids
                if cav.custom_product_template_attribute_value_id
            }

            #            custom_ptavs = {
            #                cav.custom_product_template_attribute_value_id
            #                for cav in line.product_custom_attribute_value_ids
            #                if cav.custom_product_template_attribute_value_id
            #            }

            # Atributos tipo variante
            for ptav in line.product_template_attribute_value_ids:
                if ptav.attribute_id and ptav.name:
                    descriptions.append(f"{ptav.attribute_id.name}: {ptav.name}")

            # Atributos tipo no_variant, excluyendo los que ya aparecen como custom
            for nav in line.product_no_variant_attribute_value_ids:
                if nav._origin.id in custom_ptav_ids:
                    _logger.debug(
                        "[Line %s] SKIP NO_VARIANT por estar en CUSTOM \
                              (por _origin.id) -> PTAV %s (%s)",
                        line.id,
                        nav.name,
                        nav._origin.id,
                    )
                    continue  # ya se muestra con valor
                if nav.attribute_id and nav.name:
                    descriptions.append(f"{nav.attribute_id.name}: {nav.name}")

            # Atributos personalizados con valor
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                if ptav and ptav.attribute_id:
                    attribute_name = ptav.attribute_id.name
                    value_label = cav.custom_value
                    descriptions.append(f"{attribute_name}: {ptav.name}: {value_label}")

            # Construir la descripción final
            if descriptions:
                line.name = f"{line.product_id.display_name}\n" + "\n".join(
                    descriptions
                )
            else:
                line.name = line.product_id.display_name

        return res
