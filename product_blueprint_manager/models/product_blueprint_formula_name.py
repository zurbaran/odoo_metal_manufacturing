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
    svg_element_id = fields.Char(string="ID de nodo SVG", help="ID del elemento SVG que contiene esta fórmula.")

    _sql_constraints = [
        ('unique_formula_per_node', 'unique(name, blueprint_id, svg_element_id)', 
         "Cada fórmula debe ser única por ID SVG dentro del mismo plano.")
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _logger.debug(
                f"[Blueprint][Formula Name] Creando nueva etiqueta: '{vals.get('name')}' "
                f"para plano ID: {vals.get('blueprint_id')} con color={vals.get('fill_color')} "
                f"tamaño={vals.get('font_size')} - Nodo SVG ID={vals.get('svg_element_id')}"
            )
        return super(ProductBlueprintFormulaName, self).create(vals_list)

    def write(self, vals):
        for record in self:
            _logger.debug(
                f"[Blueprint][Formula Name] Modificando etiqueta '{record.name}' "
                f"del plano ID {record.blueprint_id.id} con cambios: {vals}"
            )
        return super(ProductBlueprintFormulaName, self).write(vals)

    def unlink(self):
        for record in self:
            _logger.warning(
                f"[Blueprint][Formula Name] Eliminando etiqueta '{record.name}' "
                f"del plano ID {record.blueprint_id.id} (Nodo SVG ID={record.svg_element_id})."
            )
        return super(ProductBlueprintFormulaName, self).unlink()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        blueprint_id = self.env.context.get('blueprint_id')
        if blueprint_id:
            args += [('blueprint_id', '=', blueprint_id)]
        return super().name_search(name, args, operator=operator, limit=limit)
