from odoo import models, fields, api

class ProductBlueprint(models.Model):
    """Modelo para representar un plano de producto."""

    _name = "product.blueprint"
    _description = "Product Blueprint"

    name = fields.Char("Nombre del Plano", required=True)
    file = fields.Binary("Archivo del Plano", required=True, attachment=True)
    filename = fields.Char(
        "Nombre del Archivo", compute="_compute_filename", store=True
    )
    product_id = fields.Many2one(
        "product.template", string="Producto", required=True
    )
    formula_ids = fields.One2many(
        "product.blueprint.formula", "blueprint_id", string="Fórmulas"
    )
    #active = fields.Boolean(string="Activo", default=True)

    @api.depends("file", "name")
    def _compute_filename(self):
        """Calcula el nombre del archivo basado en el nombre del plano."""
        for record in self:
            if record.file and record.name:
                record.filename = record.name + ".svg"
            else:
                record.filename = ""
