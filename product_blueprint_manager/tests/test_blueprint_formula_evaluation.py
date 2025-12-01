from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintFormulaEvaluation(TransactionCase):
    """
    Conjunto de tests para verificar el comportamiento del método
    `_safe_evaluate_formula` definido en el modelo
    `product.blueprint.formula.name`.

    Estos tests comprueban:
      - Que una expresión válida se evalúa correctamente.
      - Que una expresión inválida (ej. división por cero) devuelve "Error"
        en lugar de lanzar una excepción.
    """

    def test_safe_evaluate_valid_expression(self):
        """
        Verifica que una expresión aritmética simple y válida
        se evalúa correctamente y devuelve el resultado esperado
        como cadena.
        """
        # Obtenemos el modelo que implementa `_safe_evaluate_formula`
        formula = self.env["product.blueprint.formula.name"]
        # Evaluamos una expresión sencilla sin variables
        result = formula._safe_evaluate_formula("2 + 2", {})
        # El método debe devolver el resultado numérico como string
        self.assertEqual(result, "4")

    def test_safe_evaluate_invalid_expression(self):
        """
        Verifica que una expresión inválida (en este caso, división por cero)
        no lanza una excepción hacia el test y en su lugar devuelve
        la cadena "Error".
        """
        # Obtenemos el modelo que implementa `_safe_evaluate_formula`
        formula = self.env["product.blueprint.formula.name"]
        # Esta expresión genera un error en tiempo de evaluación (ZeroDivisionError)
        result = formula._safe_evaluate_formula("2 / 0", {})
        # El contrato del método indica que debe devolver "Error" ante fallos
        self.assertEqual(result, "Error")
