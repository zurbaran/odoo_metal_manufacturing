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
        # domain="[('blueprint_id', '=', blueprint_id)]",  # Dominio base, se modifica dinámicamente
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
        """Actualizar las opciones de nombres de fórmula cuando se cambia el plano."""
        self.name = False  # Resetear selección si cambiamos de plano
        return {'domain': {'name': self._get_available_formula_names_domain()}}
    
    def _get_available_formula_names_domain(self):
        """Calcula el dominio para el campo name."""
        if self.blueprint_id:
            # Obtener todos los nombres de fórmula posibles para el plano actual.
            all_formula_names = self.env["product.blueprint.formula.name"].search([("blueprint_id", "=", self.blueprint_id.id)]).mapped("id")

            # Obtener los nombres de fórmula YA USADOS en fórmulas *existentes* de este plano
            # (usamos `search` en lugar de `self.blueprint_id.formula_ids` para incluir
            #  todas las formulas, no solo las del record actual).
            used_formula_names = self.env["product.blueprint.formula"].search([
                ("blueprint_id", "=", self.blueprint_id.id),
                ("id", "!=", self.id if self.id else False)  # Excluir la fórmula actual (si existe)
                ]).mapped("name").mapped("id")

            # Filtrar los nombres disponibles:  todos - los usados
            available_formula_names = list(set(all_formula_names) - set(used_formula_names))

            _logger.info(f"[Blueprint][Formula] Etiquetas disponibles (filtradas): {available_formula_names}")
            return [("id", "in", available_formula_names)]  # Usar 'id' en el dominio

        else:
            _logger.info(f"[Blueprint][Formula] No se ha seleccionado ningún plano.")
            return [("id", "in", [])]

    @api.model
    def default_get(self, fields):
        """Establecer el dominio por defecto al crear un nuevo registro."""
        res = super().default_get(fields)
        if 'name' in fields:  # Solo si el campo 'name' se está inicializando
            res.update({'domain_name': self._get_available_formula_names_domain()})  # Usar domain_name
        return res


    _sql_constraints = [
        ('unique_formula_per_blueprint', 'unique(name, blueprint_id)', 'Ya existe una fórmula configurada para esta etiqueta en este plano.'),
    ]