from odoo import api, fields, models  # pyright: ignore[reportMissingImports]

# ---------------------------------------------------------------------------
# Modelo: product.blueprint.condition
# ---------------------------------------------------------------------------
# Este modelo define las "condiciones" que debe cumplir un producto para que
# un plano (product.blueprint) aplique en una línea de pedido.
#
# Cada registro indica:
#   - Un plano concreto (blueprint_id)
#   - Un atributo del producto (attribute_id)
#   - Uno o varios valores permitidos de ese atributo (value_ids)
#
# Durante la generación de planos en sale.order.line, estas condiciones se
# consultan para decidir qué planos son válidos según los atributos elegidos.
# ---------------------------------------------------------------------------


class ProductBlueprintCondition(models.Model):
    _name = "product.blueprint.condition"
    _description = "Condición del Plano de Producto"

    # -----------------------------------------------------------------------
    # CAMPOS BÁSICOS
    # -----------------------------------------------------------------------

    # Plano al que pertenece esta condición.
    # Se borra en cascada si se elimina el plano principal.
    blueprint_id = fields.Many2one(
        "product.blueprint",
        string="Plano",
        required=True,
        ondelete="cascade",
    )

    # Atributo del producto sobre el que se aplica la condición
    # (por ejemplo: Vidrio, Acabado, Color, etc.).
    attribute_id = fields.Many2one(
        "product.attribute",
        string="Atributo",
        required=True,
    )

    # Conjunto de valores permitidos para el atributo seleccionado.
    # El plano solo será válido si la línea de venta tiene al menos
    # uno de estos valores para el atributo indicado.
    value_ids = fields.Many2many(
        "product.attribute.value",
        string="Valores",
    )

    # Producto asociado al plano (derivado del plano).
    # Es solo de lectura porque se obtiene del blueprint_id.
    product_id = fields.Many2one(
        "product.template",
        string="Producto",
        related="blueprint_id.product_id",
        readonly=True,
    )

    # -----------------------------------------------------------------------
    # ONCHANGE: BLUEPRINT
    # -----------------------------------------------------------------------

    @api.onchange("blueprint_id")
    def _onchange_blueprint_id(self):
        # Si hay blueprint y producto, limitar los atributos
        # al conjunto de atributos configurados en la plantilla
        # del producto del plano. Esto evita seleccionar atributos
        # que el producto no tiene.
        if self.blueprint_id and self.blueprint_id.product_id:
            attribute_ids = self.blueprint_id.product_id.attribute_line_ids.mapped(
                "attribute_id"
            ).ids
            return {
                "domain": {
                    # Solo atributos presentes en la plantilla del producto
                    "attribute_id": [("id", "in", attribute_ids)],
                    # Solo valores asociados a los mismos atributos
                    "value_ids": [("attribute_id", "in", attribute_ids)],
                }
            }
        # Si no hay blueprint/producto, vacía los fields y el dominio
        # para obligar al usuario a volver a seleccionar cuando se
        # defina un plano válido.
        self.attribute_id = False
        self.value_ids = False
        return {
            "domain": {
                "attribute_id": [("id", "=", False)],
                "value_ids": [("id", "=", False)],
            }
        }

    # -----------------------------------------------------------------------
    # ONCHANGE: ATRIBUTO
    # -----------------------------------------------------------------------

    @api.onchange("attribute_id")
    def _onchange_attribute_id(self):
        # Limita valores solo a los del atributo seleccionado
        # para evitar mezclar valores de otros atributos.
        if self.attribute_id:
            return {
                "domain": {"value_ids": [("attribute_id", "=", self.attribute_id.id)]}
            }
        # Si se limpia el atributo, también se limpian los valores y
        # se cierra el dominio para obligar a una selección válida.
        self.value_ids = False
        return {"domain": {"value_ids": [("id", "=", False)]}}
