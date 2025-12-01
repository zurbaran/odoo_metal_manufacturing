from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase

# Módulo de pruebas unitarias para la lógica de cálculo de incrementos de precio
# mediante fórmulas en product.template.attribute.value.
# Aquí se valida el comportamiento del método público
# `calculate_price_increment`, cubriendo distintos casos de uso:
#   - Fórmula simple con custom_value
#   - Ausencia de fórmula (uso de price_extra)
#   - Resultado negativo
#   - Errores de sintaxis/ejecución en la fórmula
#   - Uso de funciones matemáticas (math)
#   - Uso de la variable price_so_far


class TestPriceFormula(SavepointCase):
    """Tests de la funcionalidad de cálculo de incremento de precio por fórmula
    en los valores de atributos de plantilla de producto.
    """

    def test_calculate_price_increment_formula(self):
        """Debe aplicar correctamente una fórmula simple basada en custom_value.

        Fórmula configurada:
            custom_value * 2

        Para custom_value = 10 el incremento esperado es 20.
        """
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Length",
                "price_formula": "custom_value * 2",
                "price_extra": 0,
            }
        )
        # 10 * 2 = 20
        self.assertEqual(ptav.calculate_price_increment(10, 0), 20)

    def test_calculate_price_increment_no_formula(self):
        """Si no hay fórmula, debe usarse price_extra como incremento fijo.

        En este caso price_formula es False, por lo que el método debe devolver
        exactamente el valor de price_extra, independientemente de custom_value.
        """
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Width",
                "price_formula": False,
                "price_extra": 5,
            }
        )
        # Al no haber fórmula, el incremento debe ser 5 (price_extra).
        self.assertEqual(ptav.calculate_price_increment(10, 0), 5)

    def test_calculate_price_increment_negative(self):
        """Un resultado negativo debe normalizarse a 0.

        Fórmula configurada:
            custom_value - 50

        Para custom_value = 10:
            10 - 50 = -40  → incremento esperado = 0
        """
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Size",
                "price_formula": "custom_value - 50",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(10, 0), 0)

    def test_calculate_price_increment_error(self):
        """Errores en la fórmula deben lanzar ValidationError.

        Fórmula configurada:
            custom_value /

        Es una expresión inválida (operador sin segundo operando), por lo que
        la evaluación segura debe fallar y traducirse en un ValidationError.
        """
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Broken",
                "price_formula": "custom_value /",
                "price_extra": 0,
            }
        )
        with self.assertRaises(ValidationError):
            ptav.calculate_price_increment(10, 0)

    def test_calculate_price_increment_math_functions(self):
        """Debe permitir usar funciones del módulo math, como sqrt.

        Fórmula configurada:
            sqrt(custom_value)

        Para custom_value = 9:
            sqrt(9) = 3  → incremento esperado = 3
        """
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Root",
                "price_formula": "sqrt(custom_value)",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(9, 0), 3)

    def test_calculate_price_increment_uses_price_so_far(self):
        """Debe soportar fórmulas basadas en price_so_far.

        Fórmula configurada:
            price_so_far * 0.1

        Para price_so_far = 100:
            100 * 0.1 = 10  → incremento esperado = 10

        El parámetro custom_value no se utiliza en esta fórmula, pero se pasa
        igualmente para verificar que no interfiere en el resultado.
        """
        ptav = self.env["product.template.attribute.value"].new(
            {
                "name": "Percent",
                "price_formula": "price_so_far * 0.1",
                "price_extra": 0,
            }
        )
        self.assertEqual(ptav.calculate_price_increment(10, 100), 10)
