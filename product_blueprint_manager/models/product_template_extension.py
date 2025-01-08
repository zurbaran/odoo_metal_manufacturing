from odoo import models, fields, api
import base64
from lxml import etree
import logging
import tempfile

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    blueprint_ids = fields.One2many('product.blueprint', 'product_id', string='Blueprints')
    formula_ids = fields.One2many('product.formula', 'product_id', string='Formulas')

    def get_custom_attribute_values(self, sale_order_line=None):
        return sale_order_line.blueprint_custom_values if sale_order_line else {}

    def get_attribute_variable_names(self):
        variable_names = []
        for attribute_line in self.attribute_line_ids:
            for value in attribute_line.value_ids:
                variable_names.append(value.name)
        return variable_names

    def generate_dynamic_blueprint(self):
        for product in self:
            for blueprint in product.blueprint_ids:
                if not blueprint.file:
                    _logger.warning(f"Blueprint sin archivo SVG para el producto: {product.name}")
                    continue

                svg_data = base64.b64decode(blueprint.file)
                root = etree.fromstring(svg_data)
                
                # Limpiar elementos de texto de fórmulas existentes
                for element in root.xpath('//text[contains(text(), "{") or contains(text(), "Formula") or contains(text(), "{{")]'):
                    parent = element.getparent()
                    if parent is not None:
                        parent.remove(element)

                # Mostrar fórmulas como texto sin evaluar
                for formula in product.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
                    try:
                        text_element = etree.Element(
                            "text",
                            x=str(formula.position_x * 10),  # Multiplicar por 10 para ajustar ubicación
                            y=str(formula.position_y * 10),  # Multiplicar por 10 para ajustar ubicación
                            fill="gray",  # Gris para indicar fórmula sin evaluar
                            style="font-size:1000px; font-family:Arial;"  # Tamaño de tipografía ajustado a 1000px
                        )
                        text_element.text = f"{{{{ {formula.formula_expression} }}}}"
                        root.append(text_element)
                    except Exception as e:
                        _logger.error(f"Error al añadir la fórmula para {product.name}: {e}")
                        continue

                blueprint.file = base64.b64encode(etree.tostring(root)).decode('utf-8')
                _logger.info(f"Blueprint generado dinámicamente con fórmulas no evaluadas para el producto: {product.name}")

    def preview_blueprint_template(self):
        self.ensure_one()
        blueprint = self.blueprint_ids[:1]
        if not blueprint or not blueprint.file:
            return

        svg_data = base64.b64decode(blueprint.file)
        root = etree.fromstring(svg_data)

        # Visualizar la fórmula con su nombre y expresión
        for formula in self.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
            try:
                name_element = etree.Element(
                    "text",
                    x=str(formula.position_x * 10),  # Multiplicar por 10 para ajustar ubicación
                    y=str(formula.position_y * 10 - 10),  # Ajuste de posición
                    fill="blue",
                    style="font-size:1000px; font-family:Arial;"  # Tamaño de tipografía ajustado a 1000px
                )
                name_element.text = f"Name: {formula.name}"
                root.append(name_element)

                formula_element = etree.Element(
                    "text",
                    x=str(formula.position_x * 10),  # Multiplicar por 10 para ajustar ubicación
                    y=str(formula.position_y * 10),
                    fill="red",
                    style="font-size:1000px; font-family:Arial;"  # Tamaño de tipografía ajustado a 1000px
                )
                formula_element.text = f"Formula: {formula.formula_expression}"
                root.append(formula_element)
            except Exception as e:
                _logger.error(f"Error al procesar la fórmula para {self.name}: {e}")
                continue

        blueprint_svg = etree.tostring(root)

        # Depuración: guardar el SVG en un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as temp_svg_file:
            temp_svg_file.write(blueprint_svg)
            temp_svg_file_path = temp_svg_file.name
            _logger.info(f"SVG generado guardado temporalmente en: {temp_svg_file_path}")

        blueprint_svg_b64 = base64.b64encode(blueprint_svg).decode('utf-8')
        report_action = self.env.ref('product_blueprint_manager.action_report_blueprint_template').report_action(self, data={'blueprint_svg': blueprint_svg_b64})
        return report_action

    def generate_final_blueprint(self, sale_order_line):
        self.ensure_one()
        blueprint = self.blueprint_ids[:1]
        if not blueprint or not blueprint.file:
            return

        svg_data = base64.b64decode(blueprint.file)
        root = etree.fromstring(svg_data)

        # Visualizar la fórmula con su nombre y expresión
        for formula in self.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
            try:
                formula_result = eval(formula.formula_expression, {}, self.get_custom_attribute_values(sale_order_line))
                text_element = etree.Element(
                    "text",
                    x=str(formula.position_x * 10),  # Multiplicar por 10 para ajustar ubicación
                    y=str(formula.position_y * 10),
                    fill="black",
                    style="font-size:1000px; font-family:Arial;"  # Tamaño de tipografía ajustado a 1000px
                )
                text_element.text = str(formula_result)
                root.append(text_element)
            except Exception as e:
                _logger.error(f"Error al procesar la fórmula para {self.name}: {e}")
                continue

        blueprint_svg = etree.tostring(root)

        # Depuración: guardar el SVG en un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as temp_svg_file:
            temp_svg_file.write(blueprint_svg)
            temp_svg_file_path = temp_svg_file.name
            _logger.info(f"SVG generado guardado temporalmente en: {temp_svg_file_path}")

        blueprint_svg_b64 = base64.b64encode(blueprint_svg).decode('utf-8')
        report_action = self.env.ref('product_blueprint_manager.action_report_final_blueprint').report_action(self, data={'blueprint_svg': blueprint_svg_b64})
        return report_action
