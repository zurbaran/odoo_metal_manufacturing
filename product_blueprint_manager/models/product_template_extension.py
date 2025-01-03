from odoo import models, fields, api
import base64
from lxml import etree
import logging

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

                for formula in product.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
                    try:
                        text_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y))
                        text_element.text = f'{{{{ {formula.formula_expression} }}}}'
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

        for formula in self.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
            try:
                # Añadir el nombre de la fórmula
                name_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y - 10), fill="blue")
                name_element.text = f'Name: {formula.name}'
                root.append(name_element)

                # Añadir la fórmula sin evaluar
                formula_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y), fill="red")
                formula_element.text = f'Formula: {formula.formula_expression}'
                root.append(formula_element)
            except Exception as e:
                _logger.error(f"Error al procesar la fórmula para {self.name}: {e}")
                continue

        blueprint_svg = base64.b64encode(etree.tostring(root)).decode('utf-8')
        report_action = self.env.ref('product_blueprint_manager.action_report_blueprint_template').report_action(self, data={'blueprint_svg': blueprint_svg})
        return report_action

    def generate_final_blueprint(self, sale_order_line):
        self.ensure_one()
        blueprint = self.blueprint_ids[:1]
        if not blueprint or not blueprint.file:
            return

        svg_data = base64.b64decode(blueprint.file)
        root = etree.fromstring(svg_data)

        for formula in self.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
            try:
                formula_result = eval(formula.formula_expression, {}, self.get_custom_attribute_values(sale_order_line))
                text_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y), fill="black")
                text_element.text = str(formula_result)
                root.append(text_element)
            except Exception as e:
                _logger.error(f"Error al procesar la fórmula para {self.name}: {e}")
                continue

        blueprint_svg = base64.b64encode(etree.tostring(root)).decode('utf-8')
        report_action = self.env.ref('product_blueprint_manager.action_report_final_blueprint').report_action(self, data={'blueprint_svg': blueprint_svg})
        return report_action
