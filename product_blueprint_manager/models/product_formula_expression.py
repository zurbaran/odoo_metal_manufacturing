from odoo import models, fields

class ProductFormulaExpression(models.Model):
    _name = 'product.formula.expression'
    _description = 'Product Formula Expression'

    name = fields.Char('Expression', required=True)
