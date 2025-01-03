from odoo import models, fields, api

class ProductFormula(models.Model):
    _name = 'product.formula'
    _description = 'Product Formula'

    name = fields.Char('Formula Name', required=True)
    formula_expression = fields.Char('Formula Expression', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
    blueprint_id = fields.Many2one('product.blueprint', string='Blueprint', required=True, help="El blueprint al que pertenece esta fórmula.")
    position_x = fields.Float('Position X', required=True, help="La coordenada X para posicionar la fórmula en el plano.")
    position_y = fields.Float('Position Y', required=True, help="La coordenada Y para posicionar la fórmula en el plano.")

    available_attributes = fields.Char(string="Available Attributes", compute="_compute_available_attributes")

    @api.depends('product_id')
    def _compute_available_attributes(self):
        for record in self:
            if record.product_id:
                variable_names = record.product_id.get_attribute_variable_names()
                record.available_attributes = ', '.join(variable_names)
            else:
                record.available_attributes = ''
