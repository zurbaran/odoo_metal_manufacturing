from odoo import models, fields, api, _
import base64
from lxml import etree
import logging
import ast
import math

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    blueprint_custom_values = fields.Char(
        compute="_capture_blueprint_custom_values",
        string="Blueprint Custom Values",
    )

    @api.depends("product_id", "product_custom_attribute_value_ids")
    def _capture_blueprint_custom_values(self):
        hook = self.env["product.blueprint.hook"]
        for line in self:
            _logger.info(f"[Blueprint] Capturando valores para la línea de pedido {line.id}")
            blueprint_custom_values = hook.get_attribute_values_for_blueprint(line)
            line.blueprint_custom_values = str(blueprint_custom_values)

    def _generate_evaluated_blueprint_svg(self, blueprint, variables=None):
        """
        Genera un SVG con los resultados de las fórmulas evaluadas.
        No modifica el archivo original del plano.
        """
        _logger.info(f"[Blueprint] Generando SVG para el plano '{blueprint.name}'.")

        try:
            # Cargar el SVG original sin modificarlo
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            # Detectar espacio de nombres (namespace)
            nsmap = {'svg': root.nsmap.get(None, 'http://www.w3.org/2000/svg')}
            _logger.debug(f"[Blueprint] Espacios de nombres detectados: {nsmap}")

            # Buscar y reemplazar las etiquetas <text class="odoo-formula">
            for text_element in root.xpath("//svg:text[contains(@class, 'odoo-formula')]", namespaces=nsmap):
                formula_name = "".join(text_element.xpath("string(.)", namespaces=nsmap)).strip()
                _logger.info(f"[Blueprint] Procesando etiqueta: '{formula_name}'")

                # Buscar la fórmula asociada
                formula = blueprint.formula_ids.filtered(lambda f: f.name.name == formula_name)
                if not formula:
                    _logger.warning(f"[Blueprint] No se encontró fórmula asociada a '{formula_name}'.")
                    continue

                try:
                    # Evaluar la fórmula
                    result = self.safe_evaluate_formula(formula.formula_expression, variables)
                    _logger.info(f"[Blueprint] Resultado para '{formula_name}': {result}")

                    # Reemplazar el contenido del texto sin perder el formato
                    for tspan in text_element.xpath(".//svg:tspan", namespaces=nsmap):
                        tspan.text = str(result)
                    if not text_element.xpath(".//svg:tspan", namespaces=nsmap):
                        text_element.text = str(result)

                except Exception as e:
                    _logger.exception(f"[Blueprint] Error al evaluar la fórmula '{formula_name}': {e}")
                    text_element.text = "Error"

            # Convertir el SVG modificado en base64 para el PDF
            final_svg = etree.tostring(root, encoding="utf-8").decode()
            _logger.info(f"[Blueprint] SVG generado con éxito para '{blueprint.name}'.")
            return base64.b64encode(final_svg.encode()).decode()

        except Exception as e:
            _logger.exception(f"[Blueprint] Error al procesar el SVG: {e}")
            return blueprint.file

    def safe_evaluate_formula(self, expression, variables):
        """
        Evalúa de manera segura la fórmula usando solo las variables permitidas.

        Args:
            expression (str): La expresión matemática a evaluar (ej. "mmA * 2").
            variables (dict): Diccionario con los valores de las variables (ej. {"mmA": 1500}).

        Returns:
            str: Resultado de la evaluación o 'Error' si ocurre un problema.
        """
        _logger.info(f"[Blueprint] Evaluando expresión: '{expression}' con variables: {variables}")

        try:
            # Crear entorno seguro con funciones matemáticas permitidas
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            allowed_names.update(variables)  # Agregar variables de la línea de venta

            # Analizar la expresión de forma segura
            tree = ast.parse(expression, mode='eval')
            compiled = compile(tree, "<string>", "eval")

            result = eval(compiled, {"__builtins__": {}}, allowed_names)

            _logger.info(f"[Blueprint] Resultado de la evaluación: {result}")
            return str(result)  # Convertimos a string para evitar errores con tipos de datos

        except Exception as e:
            _logger.exception(f"[Blueprint] Error al evaluar la fórmula '{expression}': {e}")
            return "Error"
        
    def _get_evaluated_variables(self, sale_order_line):
        """
        Devuelve un diccionario con los nombres de las variables personalizadas y sus valores correspondientes.

        Args:
            sale_order_line (recordset): La línea de pedido de venta.

        Returns:
            dict: Un diccionario con las variables evaluadas.
        """
        _logger.info(
            f"[Blueprint] Iniciando la captura de variables evaluadas para la línea de venta ID: {sale_order_line.id}, Producto: {sale_order_line.product_id.name if sale_order_line.product_id else 'Ninguno'}"
        )

        hook = self.env["product.blueprint.hook"]
        attribute_values = hook.get_attribute_values_for_blueprint(sale_order_line)
        _logger.info(
            f"[Blueprint] Atributos capturados para la línea {sale_order_line.id}: {attribute_values}"
        )

        variable_mapping = {}

        if (
            not sale_order_line.product_id
            or not sale_order_line.product_id.product_tmpl_id
        ):
            _logger.warning(
                f"[Blueprint] Producto o plantilla de producto no encontrado para la línea {sale_order_line.id}."
            )
            return {}

        formula_count = len(sale_order_line.product_id.product_tmpl_id.formula_ids)
        _logger.info(
            f"[Blueprint] Se encontraron {formula_count} fórmula(s) para el producto '{sale_order_line.product_id.name}'."
        )

        for formula in sale_order_line.product_id.product_tmpl_id.formula_ids:
            _logger.info(
                f"[Blueprint] Procesando fórmula: '{formula.name}' para el blueprint '{formula.blueprint_id.name or 'N/A'}'"
            )

            if not formula.formula_expression:
                _logger.warning(
                    f"[Blueprint] Fórmula sin expresión para '{formula.name}' en la línea {sale_order_line.id}."
                )
                continue

            if not formula.available_attributes:
                _logger.warning(
                    f"[Blueprint] La fórmula '{formula.name}' no tiene atributos disponibles definidos."
                )
                continue

            _logger.info(
                f"[Blueprint] Atributos disponibles para la fórmula '{formula.name}': {formula.available_attributes}"
            )

            for attribute_name in formula.available_attributes.split(","):
                attribute_name = attribute_name.strip()
                if attribute_name in attribute_values:
                    try:
                        variable_mapping[attribute_name] = float(
                            attribute_values[attribute_name]
                        )
                        _logger.info(
                            f"[Blueprint] Atributo '{attribute_name}' encontrado con valor: {variable_mapping[attribute_name]}"
                        )
                    except ValueError:
                        variable_mapping[attribute_name] = attribute_values[
                            attribute_name
                        ]
                        _logger.warning(
                            f"[Blueprint] Atributo '{attribute_name}' no es un número. Se usará como cadena: '{attribute_values[attribute_name]}'"
                        )
                else:
                    _logger.warning(
                        f"[Blueprint] Atributo '{attribute_name}' no encontrado en los valores de atributos para la línea {sale_order_line.id}."
                    )

        if not variable_mapping:
            _logger.warning(
                f"[Blueprint] No se mapearon variables para la línea {sale_order_line.id}."
            )
        else:
            _logger.info(
                f"[Blueprint] Variables mapeadas para la línea {sale_order_line.id}: {variable_mapping}"
            )

        _logger.info(
            f"[Blueprint] Finalizada la captura de variables para la línea {sale_order_line.id}."
        )
        return variable_mapping
