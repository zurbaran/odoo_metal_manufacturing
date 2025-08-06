from odoo import api, fields, models


class ProductBlueprintCondition(models.Model):
    _name = "product.blueprint.condition"
    _description = "Condición del Plano de Producto"

    blueprint_id = fields.Many2one(
        "product.blueprint",
        string="Plano",
        required=True,
        ondelete="cascade",
    )
    attribute_id = fields.Many2one(
        "product.attribute",
        string="Atributo",
        required=True,
    )
    value_ids = fields.Many2many(
        "product.attribute.value",
        string="Valores",
    )
    product_id = fields.Many2one(
        "product.template",
        string="Producto",
        related="blueprint_id.product_id",
        readonly=True,
    )

    @api.onchange("blueprint_id")
    def _onchange_blueprint_id(self):
        if self.blueprint_id and self.blueprint_id.product_id:
            attribute_ids = (
                self.blueprint_id.product_id.attribute_line_ids.mapped(
                    "attribute_id"
                ).ids
            )
            return {"domain": {"attribute_id": [("id", "in", attribute_ids)]}}
        self.attribute_id = False
        self.value_ids = False
        return {
            "domain": {
                "attribute_id": [("id", "=", False)],
                "value_ids": [("id", "=", False)],
            }
        }

    @api.onchange("attribute_id")
    def _onchange_attribute_id(self):
        if self.attribute_id:
            return {
                "domain": {
                    "value_ids": [
                        ("attribute_id", "=", self.attribute_id.id)
                    ]
                }
            }
        self.value_ids = False
        return {"domain": {"value_ids": [("id", "=", False)]}}

