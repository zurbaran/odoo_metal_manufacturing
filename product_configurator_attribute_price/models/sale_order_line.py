import logging
import math

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """
    Hereda de sale.order.line para modificar el cálculo del precio unitario
    considerando las fórmulas de los atributos.
    """

    _inherit = "sale.order.line"

    price_modified = fields.Monetary(
        string="Precio Modificado",
        currency_field="currency_id",
        compute="_compute_price_modified",
        store=False,
    )

    @api.depends(
        "product_id",
        "custom_value_ids",
        "config_session_id",
        "config_session_id.value_ids",
    )
    def _compute_price_unit(self):
        """
        Calcula el precio unitario, aplicando fórmulas y ajustes específicos
        para atributos configurables.
        """
        result = super()._compute_price_unit()

        ptav_model = self.env["product.template.attribute.value"]
        try:
            custom_ptav = self.env.ref("product_configurator.custom_attribute_value")
        except Exception:  # pragma: no cover - ref not found if dependency missing
            custom_ptav = None

        for line in self:
            if not line.product_id:
                _logger.warning(
                    "[Line %s] Producto no definido. Saltando cálculo.", line.id
                )
                continue

            price_so_far = line.price_unit
            _logger.debug(f"[Line {line.id}] Precio inicial: {price_so_far}")
            tmpl = line.product_id.product_tmpl_id

            # Procesar valores personalizados
            for custom_value in line.custom_value_ids:
                if not custom_ptav:
                    continue
                ptav = ptav_model.search(
                    [
                        ("product_tmpl_id", "=", tmpl.id),
                        ("attribute_id", "=", custom_value.attribute_id.id),
                        ("product_attribute_value_id", "=", custom_ptav.id),
                    ],
                    limit=1,
                )
                if ptav and ptav.price_formula and "custom_value" in ptav.price_formula:
                    try:
                        custom_val = float(custom_value.eval())
                        increment = eval(
                            ptav.price_formula,
                            {"__builtins__": None},
                            {
                                "custom_value": custom_val,
                                "price_so_far": price_so_far,
                                "math": math,
                            },
                        )
                        if increment < 0:
                            increment = 0
                        price_so_far += increment
                        _logger.debug(
                            "[Line %s] Incremento por custom_value (%s): %s",
                            line.id,
                            ptav.name,
                            increment,
                        )
                    except Exception as e:
                        _logger.exception(
                            "[Line %s] Error al evaluar la fórmula para %s: %s",
                            line.id,
                            ptav.name if ptav else "?",
                            e,
                        )

            # Procesar atributos con price_so_far
            for value in line.config_session_id.value_ids:
                ptav = ptav_model.search(
                    [
                        ("product_tmpl_id", "=", tmpl.id),
                        ("product_attribute_value_id", "=", value.id),
                    ],
                    limit=1,
                )
                if ptav and ptav.price_formula and "price_so_far" in ptav.price_formula:
                    try:
                        increment = eval(
                            ptav.price_formula,
                            {"__builtins__": None},
                            {"price_so_far": price_so_far, "math": math},
                        )
                        if increment < 0:
                            increment = 0
                        price_so_far += increment
                        _logger.debug(
                            "[Line %s] Incremento por price_so_far (%s): %s",
                            line.id,
                            ptav.name,
                            increment,
                        )
                    except Exception as e:
                        _logger.exception(
                            "[Line %s] Error al evaluar la fórmula para %s: %s",
                            line.id,
                            ptav.name,
                            e,
                        )

            line.price_unit = price_so_far
            _logger.info(
                "[Line %s] Precio final calculado: %s", line.id, line.price_unit
            )

        return result

    @api.depends("price_unit")
    def _compute_price_modified(self):
        for line in self:
            # Se muestra el mismo valor que price_unit, pero podrías aplicar lógica
            # adicional aquí.
            line.price_modified = line.price_unit
