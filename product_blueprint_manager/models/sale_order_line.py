from odoo import models, fields, api
import base64
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    blueprint_custom_values = fields.Char(compute='_capture_blueprint_custom_values', string='Blueprint Custom Values')

    @api.depends('product_id', 'product_custom_attribute_value_ids')
    def _capture_blueprint_custom_values(self):
        hook = self.env['product.blueprint.attribute.hook']
        for line in self:
            blueprint_custom_values = hook.get_attribute_values_for_blueprint(line)  # Usar hook para obtener valores
            self.blueprint_custom_values = blueprint_custom_values
            if hasattr(self.product_id.product_tmpl_id, 'evaluate_formulas'):
                self.product_id.product_tmpl_id.evaluate_formulas(blueprint_custom_values)

    def generate_blueprint_document(self):
        for line in self:
            if not line.product_id:
                _logger.warning(f"Producto no definido en la línea de pedido.")
                continue

            product = line.product_id.product_tmpl_id

            for blueprint in product.blueprint_ids:
                if not blueprint.file:
                    _logger.warning(f"Blueprint sin archivo SVG para el producto: {product.name}")
                    continue

                svg_data = base64.b64decode(blueprint.file)
                root = etree.fromstring(svg_data)

                for formula in product.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
                    try:
                        formula_result = eval(formula.formula_expression, {}, line.blueprint_custom_values)
                        text_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y))
                        text_element.text = str(formula_result)
                        root.append(text_element)
                    except Exception as e:
                        _logger.error(f"Error al procesar la fórmula para {product.name}: {e}")
                        continue

                svg_content = etree.tostring(root).decode('utf-8')
                pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([svg_content])
                pdf_base64 = base64.b64encode(pdf_content)

                attachment = self.env['ir.attachment'].create({
                    'name': f"{product.name}_blueprint.pdf",
                    'type': 'binary',
                    'datas': pdf_base64,
                    'res_model': 'sale.order',
                    'res_id': self.order_id.id,
                })

                _logger.info(f"Documento de blueprint generado y adjuntado al pedido de venta.")
