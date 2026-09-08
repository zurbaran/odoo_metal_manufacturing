import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..utils import evaluate_math_expression

# Logger del módulo. Se utiliza para dejar trazas de depuración e información
# sobre la evaluación de fórmulas de precio.
_logger = logging.getLogger(__name__)


class ProductTemplateAttributeValue(models.Model):
    """
    Hereda de product.template.attribute.value para agregar la funcionalidad
    de cálculo de precio por fórmula.
    """

    _inherit = "product.template.attribute.value"

    # Campo donde se define la fórmula de precio a nivel de valor de atributo.
    # Esta fórmula se evaluará dinámicamente cuando se calculen los precios de
    # las líneas de pedido (por ejemplo, en sale.order.line).
    #
    # Variables disponibles dentro de la fórmula:
    #   - custom_value: valor personalizado introducido en la cuadrícula
    #                   (por ejemplo, una medida en mm).
    #   - price_so_far: precio calculado hasta ese momento, antes de aplicar
    #                   este incremento (permite incrementos acumulativos).
    #
    # Ejemplos típicos:
    #   ((custom_value + 49) // 50 - 10) * 5
    #   (price_so_far * 0.2)
    #
    # La fórmula se evalúa de forma segura mediante _safe_eval.
    price_formula = fields.Char(
        help=(
            "Define a formula to calculate the price variation dynamically. "
            "Use 'custom_value' and 'price_so_far' as variables. "
            "Example: ((custom_value + 49) // 50 - 10) * 5"
            "or (price_so_far * 0.2)"
        ),
    )

    def _safe_eval(self, expression, variables):
        """Evalúa la fórmula con el evaluador AST explícitamente permitido.

        No ejecuta código Python. Solo admite variables numéricas, operadores
        matemáticos/comparaciones expresamente soportados y una lista cerrada
        de funciones matemáticas.
        """
        return evaluate_math_expression(expression, variables)

    def calculate_price_increment(self, custom_value, price_so_far):
        """
        Calcula el incremento de precio basado en la fórmula configurada.

        Esta función es el punto de entrada para obterner el incremento de
        precio asociado a un valor de atributo. Se utiliza en el flujo de
        cálculo de precios de las líneas de venta.

        Args:
            custom_value (float): Valor personalizado ingresado en la cuadrícula.
                Suele corresponder, por ejemplo, a una medida numérica
                introducida por el usuario (mm, cm, etc.).
            price_so_far (float): Precio calculado del producto hasta el momento,
                antes de aplicar este atributo. Permite aplicar fórmulas que
                dependan del precio acumulado.

        Returns:
            float: Incremento calculado (siempre no negativo). Si no hay
                fórmula definida, devuelve price_extra.

        Raises:
            ValidationError: Si hay un error al evaluar la fórmula (sintaxis
                incorrecta, uso de funciones no permitidas, etc.).
        """
        _logger.debug(f"Starting calculate_price_increment for attribute {self.name}")
        _logger.debug(
            f"Formula: {self.price_formula}, custom_value: {custom_value},\
              price_so_far: {price_so_far}"
        )

        # Si no existe una fórmula definida, se utiliza el comportamiento
        # estándar: devolver el incremento fijo configurado en price_extra.
        if not self.price_formula:
            _logger.info(
                f"No price formula defined for attribute {self.name}. Using\
                      price_extra: {self.price_extra}"
            )
            return self.price_extra  # Si no hay fórmula, usa el incremento fijo

        try:
            # Asegurarse de que custom_value y price_so_far sean números
            # (convertidos explícitamente a float para evitar problemas de tipo).
            custom_value = float(custom_value)
            price_so_far = float(price_so_far)

            _logger.debug(f"Evaluating formula: {self.price_formula}")
            _logger.debug(f"custom_value: {custom_value}, price_so_far: {price_so_far}")

            # Variables que se ponen a disposición de la fórmula.
            variables = {
                "custom_value": custom_value,
                "price_so_far": price_so_far,
            }

            # Evaluación segura de la fórmula definida por el usuario.
            increment = self._safe_eval(self.price_formula, variables)
            _logger.debug(f"Result of formula evaluation: {increment}")

            # Asegurarse de que el incremento no sea negativo. Si el resultado
            # calculado es menor que 0, se fuerza a 0 para evitar descuentos
            # inesperados o errores de fórmula.
            if increment < 0:
                _logger.warning(
                    f"Negative increment calculated: {increment}. Resetting to 0."
                )
                increment = 0

            _logger.info(f"Increment calculated: {increment}")
            return float(increment)
        except Exception as e:
            # Si algo falla en la evaluación, se registra el error en el log y
            # se lanza una ValidationError para informar al usuario.
            _logger.error(f"Error evaluating formula for attribute '{self.name}': {e}")
            raise ValidationError(
                _(f"Error evaluating formula for attribute '{self.name}': {e}")
            ) from e
