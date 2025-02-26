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
        domain="[('blueprint_id', '=', blueprint_id)]",
        required=True,
        help="Seleccione el nombre de la fórmula según las etiquetas del SVG."
    )
    formula_expression = fields.Char("Expresión de la Fórmula", required=True)
    product_id = fields.Many2one("product.template", string="Producto", required=True)
    blueprint_id = fields.Many2one("product.blueprint", string="Plano", required=True, ondelete="cascade")
    available_attributes = fields.Char(string="Atributos Disponibles", compute="_compute_available_attributes", store=False)

    @api.depends("product_id")
    def _compute_available_attributes(self):
        for record in self:
            if record.product_id:
                custom_attribute_values = record.product_id.valid_product_template_attribute_line_ids.mapped("attribute_id.value_ids").filtered(lambda v: v.is_custom)
                variable_names = [value.name for value in custom_attribute_values]
                record.available_attributes = ", ".join(variable_names)
            else:
                record.available_attributes = ""

    @api.onchange("blueprint_id")
    def _onchange_blueprint_id(self):
        """Actualiza las opciones disponibles basadas en las etiquetas del plano."""
        if self.blueprint_id:
            formula_names = self.env["product.blueprint.formula.name"].search([("blueprint_id", "=", self.blueprint_id.id)]).mapped("name")
            _logger.info(f"[Blueprint][Formula] Etiquetas disponibles para el plano '{self.blueprint_id.name}': {formula_names}")
            return {"domain": {"name": [("name", "in", formula_names)]}}
        else:
            _logger.warning(f"[Blueprint][Formula] No se ha seleccionado ningún plano.")
            return {"domain": {"name": []}}
