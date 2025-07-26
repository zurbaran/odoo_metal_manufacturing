import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ProductBlueprintHook(models.AbstractModel):
    _inherit = "product.configurator.attribute.hook"
    _name = "product.blueprint.hook"
    _description = "Hook for Attribute Value Retrieval"

    def get_attribute_values_for_blueprint(self, sale_order_line):
        """
        Devuelve variables para las fórmulas del blueprint:
        - Si es un valor is_custom: variable = valor personalizado.
        - Si no es is_custom, pero el atributo tiene un is_custom (como mmAltura), asignamos el valor estándar como entero.
        """
        result = {}

        # 🔹 Atributos personalizados (mmA, mmB, mmAltura)
        for val in sale_order_line.product_custom_attribute_value_ids:
            attr_value = val.custom_product_template_attribute_value_id
            if attr_value and attr_value.is_custom:
                var_name = attr_value.name
                if val.custom_value is not None:
                    try:
                        result[var_name] = int(val.custom_value)
                        _logger.debug(
                            f"[Blueprint][HOOK] Personalizado: {var_name} = {int(val.custom_value)}"
                        )
                    except Exception:
                        _logger.warning(
                            f"[Blueprint][HOOK] Valor no numérico en custom: {val.custom_value}"
                        )

        # 🔹 Valores estándar, proyectados solo si el atributo tiene is_custom relacionado
        standard_values = (
            sale_order_line.product_template_attribute_value_ids
            + sale_order_line.product_no_variant_attribute_value_ids
        ).filtered(lambda v: not v.is_custom)

        for val in standard_values:
            attr = val.attribute_id
            custom_vals = attr.value_ids.filtered(lambda v: v.is_custom)
            if not custom_vals:
                # este atributo no tiene variable de fórmula (ej: Color, Vidrio...)
                continue

            var_name = custom_vals[0].name
            if var_name in result:
                continue  # ya se ha definido manualmente

            try:
                result[var_name] = int(val.name)
                _logger.debug(
                    f"[Blueprint][HOOK] Estándar proyectado: {var_name} = {int(val.name)}"
                )
            except ValueError:
                _logger.info(
                    f"[Blueprint][HOOK] Ignorado '{val.name}' para '{var_name}': no es entero"
                )

        return result
