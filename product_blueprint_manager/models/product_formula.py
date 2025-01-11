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

    available_attributes = fields.Char(
        string="Available Attributes", 
        compute="_compute_available_attributes", 
        store=False
    )

    # # Restaurar los campos no editables para el tamaño del SVG
    # blueprint_width = fields.Float(
    #     related='blueprint_id.width', 
    #     string='Blueprint Width', 
    #     readonly=True, 
    #     store=False
    # )
    # blueprint_height = fields.Float(
    #     related='blueprint_id.height', 
    #     string='Blueprint Height', 
    #     readonly=True, 
    #     store=False
    # )



    @api.depends('product_id')
    def _compute_available_attributes(self):
        for record in self:
            if record.product_id:
                custom_attribute_values = record.product_id.valid_product_template_attribute_line_ids.mapped('attribute_id.value_ids').filtered(lambda v: v.is_custom)
                variable_names = [value.name for value in custom_attribute_values]
                record.available_attributes = ', '.join(variable_names)
            else:
                record.available_attributes = ''