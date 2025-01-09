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
            self.blueprint_custom_values = blueprint_custom_values

    def generate_blueprint_document(self):
        attachment_ids = []
        for line in self:
            product = line.product_id.product_tmpl_id
            if not product or not product.blueprint_ids:
                continue

            for blueprint in product.blueprint_ids:
                try:
                    blueprint_svg = line._generate_evaluated_blueprint_svg(blueprint)
                    if blueprint_svg:
                        pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([blueprint_svg])
                        attachment = self.env['ir.attachment'].create({
                            'name': f"{line.order_id.name}_{product.name}_blueprint.pdf",
                            'type': 'binary',
                            'datas': base64.b64encode(pdf_content),
                            'res_model': 'sale.order',
                            'res_id': line.order_id.id,
                        })
                        attachment_ids.append(attachment.id)
                except Exception as e:
                    _logger.error(f"Error generating blueprint for {product.name}: {e}")
        return attachment_ids


    def _get_evaluated_variables(self, line):
        """Retrieve evaluated variables for formula computation."""
        variables = {}
        for attr in line.product_custom_attribute_value_ids:
            variables[attr.attribute_id.name] = attr.custom_value or attr.name
        return variables

    def _attach_blueprints_to_report(self):
        """Generates and attaches blueprints before printing sale orders or invoices."""
        for line in self:
            line.generate_blueprint_document()

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        """Generate and attach blueprints when sending quotations."""
        for order in self:
            order.order_line._attach_blueprints_to_report()
        return super().action_quotation_send()

    def action_confirm(self):
        """Generate blueprints on confirmation."""
        for order in self:
            order.order_line._attach_blueprints_to_report()
        return super().action_confirm()
