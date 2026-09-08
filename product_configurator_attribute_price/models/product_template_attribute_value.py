import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..utils import evaluate_math_expression

_logger = logging.getLogger(__name__)


class ProductTemplateAttributeValue(models.Model):
    """Add formula-based price increments to template attribute values."""

    _inherit = "product.template.attribute.value"

    price_formula = fields.Char(
        help=(
            "Define a formula to calculate the price variation dynamically. "
            "Use 'custom_value' and 'price_so_far' as variables. "
            "Example: ((custom_value + 49) // 50 - 10) * 5 "
            "or (price_so_far * 0.2)"
        ),
    )

    def _safe_eval(self, expression, variables):
        """Evaluate a numeric formula through the allowlisted AST evaluator."""
        return evaluate_math_expression(expression, variables)

    def calculate_price_increment(self, custom_value, price_so_far):
        """Calculate the non-negative price increment for this attribute value."""
        _logger.debug("Starting calculate_price_increment for attribute %s", self.name)
        _logger.debug(
            "Formula: %s, custom_value: %s, price_so_far: %s",
            self.price_formula,
            custom_value,
            price_so_far,
        )

        if not self.price_formula:
            _logger.info(
                "No price formula defined for attribute %s. Using price_extra: %s",
                self.name,
                self.price_extra,
            )
            return self.price_extra

        try:
            custom_value = float(custom_value)
            price_so_far = float(price_so_far)
            variables = {
                "custom_value": custom_value,
                "price_so_far": price_so_far,
            }
            increment = self._safe_eval(self.price_formula, variables)

            if increment < 0:
                _logger.warning(
                    "Negative increment calculated: %s. Resetting to 0.", increment
                )
                increment = 0

            _logger.info("Increment calculated: %s", increment)
            return float(increment)
        except Exception as exc:
            message = _(
                "Error evaluating formula for attribute '%(name)s': %(error)s",
                name=self.name,
                error=exc,
            )
            _logger.error("%s", message)
            raise ValidationError(message) from exc
