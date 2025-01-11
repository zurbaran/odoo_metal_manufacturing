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
            blueprint_custom_values = hook.get_attribute_values_for_blueprint(line)
            _logger.info(f"[Blueprint] Captura de valores de atributos para línea {line.id}: {blueprint_custom_values}")
            line.blueprint_custom_values = blueprint_custom_values

    def generate_blueprint_document(self):
        attachment_ids = []
        for line in self:
            product = line.product_id.product_tmpl_id
            if not product or not product.blueprint_ids:
                _logger.info(f"[Blueprint] Producto {line.product_id.name} no tiene blueprints definidos.")
                continue

            for blueprint in product.blueprint_ids:
                try:
                    blueprint_svg = line._generate_evaluated_blueprint_svg(blueprint)
                    if blueprint_svg:
                        _logger.info(f"[Blueprint] Generando PDF para blueprint de producto {product.name}.")
                        pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([blueprint_svg])
                        attachment = self.env['ir.attachment'].create({
                            'name': f"{line.order_id.name}_{product.name}_blueprint.pdf",
                            'type': 'binary',
                            'datas': base64.b64encode(pdf_content),
                            'res_model': 'sale.order',
                            'res_id': line.order_id.id,
                        })
                        attachment_ids.append(attachment.id)
                        _logger.info(f"[Blueprint] Blueprint adjuntado: {attachment.name}")
                except Exception as e:
                    _logger.error(f"Error generando blueprint para {product.name}: {e}")
        return attachment_ids

    def _get_evaluated_variables(self, sale_order_line):
        """
        Devuelve un diccionario con los nombres de las variables personalizadas y sus valores correspondientes.
        """
        hook = self.env['product.blueprint.attribute.hook']
        attribute_values = hook.get_attribute_values_for_blueprint(sale_order_line)
        _logger.info(f"[Blueprint] Atributos capturados para línea {sale_order_line.id}: {attribute_values}")

        variable_mapping = {}
        for formula in sale_order_line.product_id.product_tmpl_id.formula_ids:
            if not formula.formula_expression:
                _logger.warning(f"[Blueprint] Fórmula sin expresión para {formula.name} en la línea {sale_order_line.id}.")
                continue

            for attribute_name in formula.available_attributes.split(','):
                attribute_name = attribute_name.strip()
                if attribute_name in attribute_values:
                    variable_mapping[attribute_name] = attribute_values[attribute_name]
                else:
                    _logger.warning(f"[Blueprint] Atributo '{attribute_name}' no encontrado para la línea {sale_order_line.id}.")

        _logger.info(f"[Blueprint] Variables mapeadas para la línea {sale_order_line.id}: {variable_mapping}")
        return variable_mapping if variable_mapping else {}

    def _attach_blueprints_to_report(self):
        for line in self:
            line.generate_blueprint_document()

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        for order in self:
            order.order_line._attach_blueprints_to_report()
        return super().action_quotation_send()

    def action_confirm(self):
        for order in self:
            order.order_line._attach_blueprints_to_report()
        return super().action_confirm()
