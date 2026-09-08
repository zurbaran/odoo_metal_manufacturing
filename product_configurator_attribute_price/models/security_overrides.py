from odoo import models

from ..utils import evaluate_math_expression


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    def _safe_eval(self, expression, variables):
        return evaluate_math_expression(expression, variables)
