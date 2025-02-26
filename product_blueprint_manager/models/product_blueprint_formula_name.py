from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductBlueprintFormulaName(models.Model):
    _name = "product.blueprint.formula.name"
    _description = "Nombre de Etiqueta de Fórmula"
    _order = "name asc"

    name = fields.Char(string="Nombre de la Etiqueta", required=True, help="Nombre de la etiqueta detectada en el plano SVG.")
    blueprint_id = fields.Many2one("product.blueprint", string="Plano Asociado", required=True, ondelete="cascade")

    _sql_constraints = [
        ('unique_name_blueprint', 'unique(name, blueprint_id)', "El nombre de la etiqueta debe ser único dentro de cada plano.")
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _logger.info(f"[Blueprint][Formula Name] Creando nueva etiqueta: {vals.get('name')} para plano ID: {vals.get('blueprint_id')}")
        return super(ProductBlueprintFormulaName, self).create(vals_list)

    def unlink(self):
        for record in self:
            _logger.info(f"[Blueprint][Formula Name] Eliminando etiqueta '{record.name}' del plano ID {record.blueprint_id.id}.")
        return super(ProductBlueprintFormulaName, self).unlink()
