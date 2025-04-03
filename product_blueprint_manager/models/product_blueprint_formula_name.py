from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductBlueprintFormulaName(models.Model):
    _name = "product.blueprint.formula.name"
    _description = "Nombre de Etiqueta de Fórmula"
    _order = "name asc"

    name = fields.Char(string="Nombre de la Etiqueta", required=True, help="Nombre de la etiqueta detectada en el plano SVG.")
    blueprint_id = fields.Many2one("product.blueprint", string="Plano Asociado", required=True, ondelete="cascade")
    fill_color = fields.Char(string="Color del Texto", default="#000000")
    font_size = fields.Char(string="Tamaño de Fuente", default="12px")

    _sql_constraints = [
        ('unique_name_blueprint', 'unique(name, blueprint_id)', "El nombre de la etiqueta debe ser único dentro de cada plano.")
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _logger.info(f"[Blueprint][Formula Name] Creando nueva etiqueta: '{vals.get('name')}' para plano ID: {vals.get('blueprint_id')} con color={vals.get('fill_color')} tamaño={vals.get('font_size')}")
        return super(ProductBlueprintFormulaName, self).create(vals_list)

    def write(self, vals):
        for record in self:
            _logger.info(f"[Blueprint][Formula Name] Modificando etiqueta '{record.name}' del plano ID {record.blueprint_id.id} con cambios: {vals}")
        return super(ProductBlueprintFormulaName, self).write(vals)

    def unlink(self):
        for record in self:
            _logger.info(f"[Blueprint][Formula Name] Eliminando etiqueta '{record.name}' del plano ID {record.blueprint_id.id}.")
        return super(ProductBlueprintFormulaName, self).unlink()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        blueprint_id = self.env.context.get('blueprint_id')
        if blueprint_id:
            args += [('blueprint_id', '=', blueprint_id)]
        return super().name_search(name, args, operator=operator, limit=limit)
