from odoo import models, fields, api
import base64
from lxml import etree
import logging
import tempfile

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    blueprint_custom_values = fields.Char(compute='_capture_blueprint_custom_values', string='Blueprint Custom Values')

    @api.depends('product_id', 'product_custom_attribute_value_ids')
    def _capture_blueprint_custom_values(self):
        hook = self.env['product.blueprint.attribute.hook']
        for line in self:
            _logger.info(f"[Blueprint] Capturando valores personalizados para la línea de pedido: {line.id}, Producto: {line.product_id.name if line.product_id else 'Ninguno'}")
            blueprint_custom_values = hook.get_attribute_values_for_blueprint(line)
            _logger.info(f"[Blueprint] Valores personalizados capturados (hook): {blueprint_custom_values}")
            line.blueprint_custom_values = str(blueprint_custom_values)

    def _generate_evaluated_blueprint_svg(self, blueprint, mode='final', variables=None):
        """Genera el SVG con resultados de fórmulas evaluadas o nombres para previsualización."""
        _logger.info(f"[Blueprint] Generando SVG para blueprint: {blueprint.name}, Modo: {mode}")

        # Factores de escalado para las fórmulas (ajústalos según sea necesario)
        FORMULA_POSITION_SCALE_FACTOR = 100
        FORMULA_FONT_SIZE_SCALE_FACTOR = 36.45

        try:
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            if mode not in ['final', 'preview']:
                _logger.warning(f"[Blueprint] Modo desconocido: {mode}. Por favor, use 'final' o 'preview'.")

            formulas = blueprint.formula_ids
            _logger.info(f"[Blueprint] Se encontraron {len(formulas)} fórmula(s) para el blueprint '{blueprint.name}'.")

            for formula in formulas:
                _logger.info(f"[Blueprint] Procesando fórmula: '{formula.name}' (Expr: '{formula.formula_expression}'), "
                            f"Posición: ({formula.position_x}, {formula.position_y}), "
                            f"Color: {formula.font_color}, Tamaño de Fuente: {formula.font_size}")

                try:
                    if mode == 'preview':
                        result = formula.name
                        _logger.info(f"[Blueprint] Modo 'preview': Usando el nombre de la fórmula '{formula.name}' como resultado.")
                    else:
                        _logger.info(f"[Blueprint] Modo 'final': Evaluando la fórmula '{formula.formula_expression}' para la fórmula '{formula.name}'.")
                        result = self.safe_evaluate_formula(formula.formula_expression, variables)
                        _logger.info(f"[Blueprint] Resultado evaluado para la fórmula '{formula.name}': {result}")

                    # El tamaño de la fuente ya está en mm, no necesita conversión
                    font_size_str = formula.font_size
                    try:
                        font_size = float(font_size_str)
                    except ValueError:
                        _logger.warning(f"[Blueprint] No se pudo convertir el tamaño de la fuente '{font_size_str}' a un número. Usando 4 como valor predeterminado.")
                        font_size = 4.0

                    # Las coordenadas ya están en mm, no necesitan escalado
                    x_coord = formula.position_x
                    y_coord = formula.position_y

                    # Aplicar el factor de escalado a las coordenadas y al tamaño de fuente
                    scaled_x_coord = x_coord * FORMULA_POSITION_SCALE_FACTOR
                    scaled_y_coord = y_coord * FORMULA_POSITION_SCALE_FACTOR
                    scaled_font_size = font_size * FORMULA_FONT_SIZE_SCALE_FACTOR

                    font_color = formula.font_color or 'black'
                    style_string = f"font-size:{scaled_font_size}mm; font-family:Arial; fill:{font_color};"

                    # Crear el elemento de texto
                    result_element = etree.Element(
                        "text",
                        x=str(scaled_x_coord),
                        y=str(scaled_y_coord),
                        style=style_string
                    )
                    result_element.text = str(result)
                    root.append(result_element)

                    _logger.info(f"[Blueprint] Elemento SVG creado para '{formula.name}': {etree.tostring(result_element, pretty_print=True, encoding='unicode')}")

                except Exception as e:
                    _logger.exception(f"[Blueprint] Error al procesar la fórmula '{formula.name}': {e}")

            # NO SE REALIZA NINGUNA MODIFICACIÓN AL SVG ORIGINAL
            blueprint_svg = etree.tostring(root, encoding='unicode')
            _logger.info(f"[Blueprint] SVG final generado para '{blueprint.name}' (primeros 200 caracteres): {blueprint_svg[:200]}...")

            # Depuración: guardar el SVG en un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as temp_svg_file:
                temp_svg_file.write(blueprint_svg.encode('utf-8'))
                temp_svg_file_path = temp_svg_file.name
                _logger.info(f"[Blueprint] SVG generado guardado temporalmente en: {temp_svg_file_path}")

            return base64.b64encode(blueprint_svg.encode('utf-8')).decode()

        except Exception as e:
            _logger.exception(f"[Blueprint] Error al procesar el SVG para el blueprint '{blueprint.name}': {e}")
            return blueprint.file

    def safe_evaluate_formula(self, expression, variables):
        """Evalúa de manera segura la fórmula."""
        _logger.info(f"[Blueprint] Evaluando expresión: '{expression}' con variables: {variables}")
        try:
            result = eval(expression, {"__builtins__": None}, variables)
            _logger.info(f"[Blueprint] Resultado de la evaluación: {result}")
            return result
        except Exception as e:
            _logger.exception(f"[Blueprint] Error al evaluar la fórmula '{expression}': {e}")
            return 'Error en fórmula'

    def _get_evaluated_variables(self, sale_order_line):
        """
        Devuelve un diccionario con los nombres de las variables personalizadas y sus valores correspondientes.
        """
        _logger.info(f"[Blueprint] Iniciando la captura de variables evaluadas para la línea de venta ID: {sale_order_line.id}, Producto: {sale_order_line.product_id.name if sale_order_line.product_id else 'Ninguno'}")

        hook = self.env['product.blueprint.attribute.hook']
        attribute_values = hook.get_attribute_values_for_blueprint(sale_order_line)
        _logger.info(f"[Blueprint] Atributos capturados para la línea {sale_order_line.id}: {attribute_values}")

        variable_mapping = {}
        
        if not sale_order_line.product_id or not sale_order_line.product_id.product_tmpl_id:
            _logger.warning(f"[Blueprint] Producto o plantilla de producto no encontrado para la línea {sale_order_line.id}.")
            return {}

        formula_count = len(sale_order_line.product_id.product_tmpl_id.formula_ids)
        _logger.info(f"[Blueprint] Se encontraron {formula_count} fórmula(s) para el producto '{sale_order_line.product_id.name}'.")

        for formula in sale_order_line.product_id.product_tmpl_id.formula_ids:
            _logger.info(f"[Blueprint] Procesando fórmula: '{formula.name}' para el blueprint '{formula.blueprint_id.name or 'N/A'}'")
            
            if not formula.formula_expression:
                _logger.warning(f"[Blueprint] Fórmula sin expresión para '{formula.name}' en la línea {sale_order_line.id}.")
                continue

            if not formula.available_attributes:
                _logger.warning(f"[Blueprint] La fórmula '{formula.name}' no tiene atributos disponibles definidos.")
                continue

            _logger.info(f"[Blueprint] Atributos disponibles para la fórmula '{formula.name}': {formula.available_attributes}")
            
            for attribute_name in formula.available_attributes.split(','):
                attribute_name = attribute_name.strip()
                if attribute_name in attribute_values:
                    try:
                        variable_mapping[attribute_name] = float(attribute_values[attribute_name])
                        _logger.info(f"[Blueprint] Atributo '{attribute_name}' encontrado con valor: {variable_mapping[attribute_name]}")
                    except ValueError:
                        variable_mapping[attribute_name] = attribute_values[attribute_name]
                        _logger.warning(f"[Blueprint] Atributo '{attribute_name}' no es un número. Se usará como cadena: '{attribute_values[attribute_name]}'")
                else:
                    _logger.warning(f"[Blueprint] Atributo '{attribute_name}' no encontrado en los valores de atributos para la línea {sale_order_line.id}.")

        if not variable_mapping:
            _logger.warning(f"[Blueprint] No se mapearon variables para la línea {sale_order_line.id}.")
        else:
            _logger.info(f"[Blueprint] Variables mapeadas para la línea {sale_order_line.id}: {variable_mapping}")

        _logger.info(f"[Blueprint] Finalizada la captura de variables para la línea {sale_order_line.id}.")
        return variable_mapping
