# test_formula_eval_context.py

from odoo.tests.common import TransactionCase


class TestFormulaEval(TransactionCase):
    def setUp(self):
        super().setUp()
        self.hook_model = self.env["product.template"]

    def test_eval_context_has_expected_variables(self):
        dummy_line = self.env["sale.order.line"].new({})
        ctx = dummy_line._get_eval_context()
        self.assertIn("custom_value", ctx)
        self.assertIn("price_so_far", ctx)
