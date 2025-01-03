from odoo import models, fields, api
import base64
from lxml import etree

class ProductBlueprint(models.Model):
    _name = 'product.blueprint'
    _description = 'Product Blueprint'

    name = fields.Char('Name', required=True)
    filename = fields.Char('Filename')
    file = fields.Binary('File')
    width = fields.Float('Width', compute='_compute_dimensions', store=True)
    height = fields.Float('Height', compute='_compute_dimensions', store=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)

    @api.depends('file')
    def _compute_dimensions(self):
        for blueprint in self:
            if blueprint.file:
                svg_data = base64.b64decode(blueprint.file)
                root = etree.fromstring(svg_data)
                width = root.attrib.get('width', '0').replace('mm', '').replace(',', '.')
                height = root.attrib.get('height', '0').replace('mm', '').replace(',', '.')
                blueprint.width = float(width) if width else 0
                blueprint.height = float(height) if height else 0
            else:
                blueprint.width = 0
                blueprint.height = 0
