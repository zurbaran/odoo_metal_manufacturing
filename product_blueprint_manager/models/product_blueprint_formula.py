from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProductBlueprintFormula(models.Model):
    _name = "product.blueprint.formula"
    _description = "Fórmula del Plano de Producto"

    name = fields.Many2one(
        "product.blueprint.formula.name",
        string="Nombre de la Fórmula",
        required=True,
        help="Seleccione el nombre de la fórmula según las etiquetas del SVG."
    )
    formula_expression = fields.Char("Expresión de la Fórmula", required=True)
    product_id = fields.Many2one("product.template", string="Producto", required=True)
    blueprint_id = fields.Many2one("product.blueprint", string="Plano", required=True, ondelete="cascade")
    available_attributes = fields.Char(string="Atributos Disponibles", compute="_compute_available_attributes", store=False)
    fill_color = fields.Char(string="Color del Texto")
    font_size = fields.Char(string="Tamaño de Fuente")
    available_name_ids = fields.Many2many('product.blueprint.formula.name',compute='_compute_available_name_ids',store=False)

    @api.depends("product_id")
    def _compute_available_attributes(self):
        for record in self:
            if record.product_id:
                custom_attribute_values = record.product_id.valid_product_template_attribute_line_ids.mapped("attribute_id.value_ids").filtered(lambda v: v.is_custom)
                variable_names = [value.name for value in custom_attribute_values]
                record.available_attributes = ", ".join(variable_names)
            else:
                record.available_attributes = ""

    @api.depends('blueprint_id')
    def _compute_available_name_ids(self):
        FormulaName = self.env['product.blueprint.formula.name']
        Formula = self.env['product.blueprint.formula']

        for record in self:
            if not record.blueprint_id:
                record.available_name_ids = FormulaName.browse()
                continue

            used_ids = Formula.search([
                ('blueprint_id', '=', record.blueprint_id.id)
            ]).mapped('name.id')

            available_ids = FormulaName.search([
                ('blueprint_id', '=', record.blueprint_id.id),
                ('id', 'not in', used_ids)
            ])
            record.available_name_ids = available_ids

    @api.onchange("name")
    def _onchange_name(self):
        if self.name:
            self.fill_color = self.name.fill_color
            self.font_size = self.name.font_size
            _logger.info("[Blueprint][Formula] Cargando estilos desde '%s': fill_color=%s, font_size=%s", self.name.name, self.fill_color, self.font_size)

    @api.onchange("blueprint_id")
    def _onchange_blueprint_id(self):
        if self.blueprint_id:
            domain = self._get_available_formula_names_domain(self.blueprint_id)
            _logger.info("[Blueprint][Formula] Dominio calculado para blueprint_id %s: %s", self.blueprint_id.id, domain)
            return {'domain': {'name': domain}}
        else:
            _logger.info("[Blueprint][Formula] No se ha seleccionado ningún plano.")
            return {'domain': {'name': [('id', '=', False)]}}

    def _get_available_formula_names_domain(self, blueprint):
        FormulaName = self.env['product.blueprint.formula.name']
        Formula = self.env['product.blueprint.formula']

        # Fórmulas ya asignadas a este plano
        used_ids = Formula.search([
            ('blueprint_id', '=', blueprint.id)
        ]).mapped('name.id')

        # Solo devolvemos IDs válidos para este blueprint y que no estén en uso
        available_ids = FormulaName.search([
            ('blueprint_id', '=', blueprint.id),
            ('id', 'not in', used_ids)
        ]).ids

        _logger.info("[Blueprint][Formula] Etiquetas disponibles para blueprint %s: %s", blueprint.id, available_ids)

        return [('id', 'in', available_ids)]

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("[Blueprint][Formula] Creando nuevas fórmulas: %s", vals_list)
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            _logger.info("[Blueprint][Formula] Modificando fórmula '%s' con valores: %s", rec.name.name if rec.name else '-', vals)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            _logger.info("[Blueprint][Formula] Eliminando fórmula '%s' del plano ID %s", rec.name.name if rec.name else '-', rec.blueprint_id.id)
        return super().unlink()

    _sql_constraints = [
        ('unique_formula_per_blueprint', 'unique(name, blueprint_id)', 'Ya existe una fórmula configurada para esta etiqueta en este plano.'),
    ]
