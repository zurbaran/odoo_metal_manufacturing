import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..utils import evaluate_math_expression

_logger = logging.getLogger(__name__)


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    price_formula = fields.Char(
        help=(
            "Define a formula to calculate the price variation dynamically. "
            "Use 'custom_value' and 'price_so_far' as variables. "
            "Example: ((custom_value + 49) // 50 - 10) * 5"
            "or (price_so_far * 0.2)"
        ),
    )

    def _safe_eval(self, expression, variables):
        """Evaluate formulas using the explicit allowlisted AST evaluator."""
        return evaluate_math_expression(expression, variables)

    def calculate_price_increment(self, custom_value, price_so_far):
        _logger.debug("Starting calculate_price_increment for attribute %s", self.name)

        if not self.price_formula:
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
                    "Negative increment calculated for %s: %s. Resetting to 0.",
                    self.name,
                    increment,
                )
                increment = 0
            _logger.info("Increment calculated: %s", increment)
            return float(increment)
        except Exception as exc:
            _logger.warning(
                "Error evaluating formula for attribute %r: %s",
                self.name,
                exc,
            )
            raise ValidationError(
                _("Error evaluating formula for attribute '%(name)s': %(error)s", name=self.name, error=exc)
            ) from exc
