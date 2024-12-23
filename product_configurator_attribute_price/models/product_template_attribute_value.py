from odoo import models, fields, api
from odoo.exceptions import ValidationError
import math

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    price_formula = fields.Char(
        string="Price Formula",
        help="Define a formula to calculate the price variation dynamically. Use 'custom_value' as the variable."
    )

    def calculate_price_increment(self, custom_value):
        """
        Calcula el incremento de precio basado en la fórmula configurada.
        :param custom_value: Valor personalizado ingresado en la cuadrícula.
        :return: Incremento calculado como un número flotante.
        """
        if not self.price_formula:
            return self.price_extra  # Si no hay fórmula, usa el incremento fijo

        try:
            # Asegurarse de que custom_value sea un número
            custom_value = float(custom_value)
            
            # Variables adicionales que pueden ser útiles en las fórmulas
            variables = {
                'custom_value': custom_value,
                'math': math  # Para permitir el uso de funciones de math
            }
            allowed_names = {"__builtins__": None}
            allowed_names.update(variables)
            
            increment = eval(self.price_formula, {"__builtins__": None}, allowed_names)
            
            return float(increment)
        except Exception as e:
            raise ValidationError(f"Error evaluating formula for attribute '{self.name}': {str(e)}")
