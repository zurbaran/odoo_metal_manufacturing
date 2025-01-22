from odoo import models, fields, _
from odoo.exceptions import ValidationError
import math
import logging

_logger = logging.getLogger(__name__)


class ProductTemplateAttributeValue(models.Model):
    """
    Hereda de product.template.attribute.value para agregar la funcionalidad
    de cálculo de precio por fórmula.
    """
    _inherit = 'product.template.attribute.value'

    price_formula = fields.Char(
        string="Price Formula",
        help=_(
            "Define a formula to calculate the price variation dynamically. "
            "Use 'custom_value' and 'price_so_far' as variables. "
            "Example: (math.ceil(custom_value / 50) * 50 - 950) // 50 * 4 or (price_so_far * 0.2)"
        )
    )

    def calculate_price_increment(self, custom_value, price_so_far):
        """
        Calcula el incremento de precio basado en la fórmula configurada.

        Args:
            custom_value (float): Valor personalizado ingresado en la cuadrícula.
            price_so_far (float): Precio calculado del producto hasta el momento.

        Returns:
            float: Incremento calculado.

        Raises:
            ValidationError: Si hay un error al evaluar la fórmula.
        """
        _logger.info(f"Starting calculate_price_increment for attribute {self.name}")
        _logger.info(f"Formula: {self.price_formula}, custom_value: {custom_value}, price_so_far: {price_so_far}")

        if not self.price_formula:
            _logger.info(f"No price formula defined for attribute {self.name}. Using price_extra: {self.price_extra}")
            return self.price_extra  # Si no hay fórmula, usa el incremento fijo

        try:
            # Asegurarse de que custom_value y price_so_far sean números
            custom_value = float(custom_value)
            price_so_far = float(price_so_far)

            _logger.info(f"Evaluating formula: {self.price_formula}")
            _logger.info(f"custom_value: {custom_value}, price_so_far: {price_so_far}")

            # Variables adicionales que pueden ser útiles en las fórmulas
            variables = {
                'custom_value': custom_value,
                'price_so_far': price_so_far,
                'math': math  # Para permitir el uso de funciones de math
            }
            allowed_names = {"__builtins__": None}
            allowed_names.update(variables)

            # Evaluar la fórmula
            increment = eval(self.price_formula, {"__builtins__": None}, allowed_names)
            _logger.info(f"Result of formula evaluation: {increment}")

            # Asegurarse de que el incremento no sea negativo
            if increment < 0:
                _logger.warning(f"Negative increment calculated: {increment}. Resetting to 0.")
                increment = 0

            _logger.info(f"Increment calculated: {increment}")
            return float(increment)
        except Exception as e:
            _logger.error(f"Error evaluating formula for attribute '{self.name}': {e}")
            raise ValidationError(_(f"Error evaluating formula for attribute '{self.name}': {e}"))