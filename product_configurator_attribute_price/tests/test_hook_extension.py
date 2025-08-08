# test_hook_extension.py

from odoo.tests.common import TransactionCase


class TestHookExtension(TransactionCase):
    def test_hook_is_called(self):
        template = self.env["product.template"].create(
            {
                "name": "Test Hook",
            }
        )
        line = self.env["sale.order.line"].new(
            {
                "product_id": template.id,
            }
        )
        result = template._get_formula_variables_hook(line)
        self.assertIsInstance(result, dict)
