from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintFormulaEvaluation(TransactionCase):
    def test_safe_evaluate_valid_expression(self):
        formula = self.env["product.blueprint.formula.name"]
        result = formula._safe_evaluate_formula("2 + 2", {})
        self.assertEqual(result, "4")

    def test_safe_evaluate_invalid_expression(self):
        formula = self.env["product.blueprint.formula.name"]
        result = formula._safe_evaluate_formula("2 / 0", {})
        self.assertEqual(result, "Error")
