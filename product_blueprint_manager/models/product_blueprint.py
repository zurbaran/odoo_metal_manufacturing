from odoo import models, fields, api

class ProductBlueprint(models.Model):
    _name = 'product.blueprint'
    _description = 'Product Blueprint'

    name = fields.Char('Blueprint Name', required=True)
    file = fields.Binary('Blueprint File', required=True)
    filename = fields.Char('Filename', compute='_compute_filename', store=True)
    
    @api.depends('file')
    def _compute_filename(self):
        for record in self:
            if record.file:
                record.filename = f"{record.name}.svg"
            else:
                record.filename = ''

    product_id = fields.Many2one('product.template', string='Product', required=True)
