# -----------------------------------------------------------------------------
# Modelo: product.blueprint.formula
#
# Este modelo representa una *fórmula de cálculo* asociada a un plano de producto.
# Cada registro vincula:
#   - Una etiqueta de fórmula detectada en el SVG (product.blueprint.formula.name)
#   - Una expresión de cálculo en texto (formula_expression)
#   - Un producto (product.template)
#   - Un plano concreto (product.blueprint)
#
# La expresión se evaluará en otro punto del código (línea de venta) usando
# variables obtenidas de atributos personalizados y estándar del producto.
#
# Puntos clave:
#   - name: referencia a la etiqueta detectada en el SVG (no es texto libre).
#   - formula_expression: cadena con la fórmula (ej. "mmAltura * 2").
#   - available_attributes: texto informativo para el usuario con las variables
#     disponibles (mmA, mmB, Altura, etc.), calculado dinámicamente.
#   - fill_color / font_size: permiten conservar el estilo visual detectado para
#     la fórmula dentro del SVG (comentado en el formulario).
#   - available_name_ids: ayuda a filtrar el desplegable de etiquetas que aún
#     NO han sido usadas para ese plano concreto (evita duplicados).
#
# Además:
#   - Se registran logs en create/write/unlink para auditoría y depuración.
#   - La restricción SQL impide que una misma etiqueta (name) se configure
#     dos veces en el mismo plano (blueprint_id).
# -----------------------------------------------------------------------------
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductBlueprintFormula(models.Model):
    _name = "product.blueprint.formula"
    _description = "Fórmula del Plano de Producto"

    # -------------------------------------------------------------------------
    # Campos básicos de identificación / relación
    # -------------------------------------------------------------------------

    # Nombre de la fórmula: en realidad es un Many2one hacia la etiqueta
    # detectada en el SVG (product.blueprint.formula.name). No es una cadena
    # arbitraria; fuerza a que el usuario seleccione una de las etiquetas
    # extraídas del plano asociado.
    name = fields.Many2one(
        "product.blueprint.formula.name",
        string="Nombre de la Fórmula",
        required=True,
        help="Seleccione el nombre de la fórmula según las etiquetas del SVG.",
    )

    # Expresión que se evaluará para esta etiqueta. Se interpreta en otro método
    # usando un entorno seguro (variables provenientes de atributos).
    # Ejemplos: "mmA * 2", "math.ceil(mmAltura / 50) * 50", etc.
    formula_expression = fields.Char("Expresión de la Fórmula", required=True)

    # Producto al que pertenece esta fórmula. Permite agrupar y filtrar
    # fórmulas por plantilla de producto.
    product_id = fields.Many2one(
        "product.template",
        string="Producto",
        required=True,
    )

    # Plano concreto al que pertenece la fórmula. Cada plano puede tener varias
    # fórmulas, cada una vinculada a una etiqueta del SVG.
    blueprint_id = fields.Many2one(
        "product.blueprint", string="Plano", required=True, ondelete="cascade"
    )

    # -------------------------------------------------------------------------
    # Campos auxiliares e informativos
    # -------------------------------------------------------------------------

    # Lista de variables disponibles para usar en formula_expression.
    # No se almacena en BD (store=False); se calcula al vuelo a partir de los
    # atributos personalizados del producto.
    # Estructura típica: "mmA, mmB, Altura", etc.
    available_attributes = fields.Char(
        string="Atributos Disponibles",
        compute="_compute_available_attributes",
        store=False,
    )

    # Estilo visual detectado o configurado para el texto resultante de la
    # fórmula dentro del SVG. Permite preservar color original del plano
    # o ajustar manualmente si el auto-detectado no es correcto.
    fill_color = fields.Char(string="Color del Texto")

    # Tamaño de la fuente para el texto de la fórmula. Igual que fill_color,
    # puede venir auto-detectado del SVG o ser ajustado manualmente.
    font_size = fields.Char(string="Tamaño de Fuente")

    # Conjunto de etiquetas de fórmula (product.blueprint.formula.name)
    # que siguen disponibles para este blueprint. Se usa para limitar el
    # desplegable de "name" de forma que no aparezcan etiquetas ya usadas
    # en otras fórmulas del mismo plano.
    available_name_ids = fields.Many2many(
        "product.blueprint.formula.name",
        compute="_compute_available_name_ids",
        store=False,
    )

    # -------------------------------------------------------------------------
    # Cómputo de atributos disponibles para la fórmula
    # -------------------------------------------------------------------------

    @api.depends("product_id")
    def _compute_available_attributes(self):
        """
        Calcula la cadena 'available_attributes' en función del producto.

        Lógica:
          - Obtiene todos los valores de atributos de la plantilla que
            estén marcados como is_custom=True.
          - Extrae sus nombres (que son los identificadores de variables
            a usar en las fórmulas: mmA, mmB, mmAltura, etc.).
          - Une esos nombres en una cadena separada por comas para mostrarla
            al usuario como ayuda visual en el formulario.
        """
        for record in self:
            if record.product_id:
                # Usamos valid_product_template_attribute_line_ids para ajustarnos
                # al subconjunto válido para combinación (lo que Odoo considera
                # líneas de atributos aptas para variantes).
                custom_attribute_values = (
                    record.product_id.valid_product_template_attribute_line_ids.mapped(
                        "attribute_id.value_ids"
                    ).filtered(lambda v: v.is_custom)
                )
                # Los nombres de estos valores son los identificadores de variables
                # que el usuario puede emplear en formula_expression.
                variable_names = [value.name for value in custom_attribute_values]
                record.available_attributes = ", ".join(variable_names)
            else:
                # Sin producto, no hay atributos ni variables sugeridas.
                record.available_attributes = ""

    # -------------------------------------------------------------------------
    # Cómputo de etiquetas de fórmula disponibles para este plano
    # -------------------------------------------------------------------------

    @api.depends("blueprint_id")
    def _compute_available_name_ids(self):
        """
        Calcula el conjunto de 'available_name_ids' para el formulario.

        Objetivo:
          - Evitar que se pueda escoger una etiqueta (name) que ya tenga
            una fórmula configurada para el mismo plano.
        """
        FormulaName = self.env["product.blueprint.formula.name"]
        Formula = self.env["product.blueprint.formula"]

        for record in self:
            # Sin plano, no podemos restringir por blueprint: devolvemos vacío.
            if not record.blueprint_id:
                record.available_name_ids = FormulaName.browse()
                continue

            # IDs de etiquetas ya utilizadas en fórmulas del mismo plano
            used_ids = Formula.search(
                [("blueprint_id", "=", record.blueprint_id.id)]
            ).mapped("name.id")

            # Etiquetas detectadas en ese plano que aún no han sido usadas
            available_ids = FormulaName.search(
                [
                    ("blueprint_id", "=", record.blueprint_id.id),
                    ("id", "not in", used_ids),
                ]
            )
            record.available_name_ids = available_ids

    # -------------------------------------------------------------------------
    # Onchange: cuando cambia el nombre (etiqueta) de la fórmula
    # -------------------------------------------------------------------------

    @api.onchange("name")
    def _onchange_name(self):
        """
        Al cambiar la etiqueta de la fórmula, arrastramos el estilo detectado.

        Esto permite:
          - Que al seleccionar un 'name' procedente de product.blueprint.formula.name,
            se copien automáticamente sus valores de fill_color y font_size,
            manteniendo el estilo visual con el que se detectó en el SVG.
        """
        if self.name:
            self.fill_color = self.name.fill_color
            self.font_size = self.name.font_size
            _logger.debug(
                (
                    "[Blueprint][Formula] Cargando estilos desde '%s': "
                    "fill_color=%s, font_size=%s"
                ),
                self.name.name,
                self.fill_color,
                self.font_size,
            )

    # -------------------------------------------------------------------------
    # Onchange: cuando cambia el plano
    # -------------------------------------------------------------------------

    @api.onchange("blueprint_id")
    def _onchange_blueprint_id(self):
        """
        Al cambiar el plano, se recalcula el dominio del campo 'name'.

        Lógica:
          - Llama a _get_available_formula_names_domain para obtener las
            etiquetas que todavía no han sido utilizadas en este plano.
          - Devuelve un dominio dinámico usado por el cliente web de Odoo
            para filtrar las opciones del Many2one 'name'.
        """
        if self.blueprint_id:
            domain = self._get_available_formula_names_domain(self.blueprint_id)
            _logger.debug(
                ("[Blueprint][Formula] Dominio calculado para " "blueprint_id %s: %s"),
                self.blueprint_id.id,
                domain,
            )
            return {"domain": {"name": domain}}
        else:
            # Si se borra el plano, vaciamos el dominio para no sugerir nada.
            _logger.debug("[Blueprint][Formula] No se ha seleccionado ningún plano.")
            return {"domain": {"name": [("id", "=", False)]}}

    # -------------------------------------------------------------------------
    # Dominio de etiquetas de fórmula disponibles para un blueprint concreto
    # -------------------------------------------------------------------------

    def _get_available_formula_names_domain(self, blueprint):
        """
        Devuelve el dominio que limita las etiquetas de fórmula (name)
        disponibles para un blueprint dado.

        Args:
            blueprint (product.blueprint): plano para el que se buscan
                etiquetas de fórmula disponibles.

        Returns:
            list: dominio Odoo para aplicar sobre el Many2one 'name'.
        """
        FormulaName = self.env["product.blueprint.formula.name"]
        Formula = self.env["product.blueprint.formula"]

        # Fórmulas ya asignadas a este plano (evitamos que se repitan).
        used_ids = Formula.search([("blueprint_id", "=", blueprint.id)]).mapped(
            "name.id"
        )

        # Solo devolvemos IDs válidos para este blueprint y que no estén en uso
        available_ids = FormulaName.search(
            [
                ("blueprint_id", "=", blueprint.id),
                ("id", "not in", used_ids),
            ]
        ).ids

        _logger.debug(
            ("[Blueprint][Formula] Etiquetas disponibles para " "blueprint %s: %s"),
            blueprint.id,
            available_ids,
        )

        # Dominio estándar para Many2one: id dentro del conjunto disponible
        return [("id", "in", available_ids)]

    # -------------------------------------------------------------------------
    # Hooks create/write/unlink con logging para trazabilidad
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescritura de create para registrar en log las fórmulas creadas.

        No altera la lógica funcional, simplemente añade trazas de:
          - Datos recibidos
          - Cantidad de fórmulas generadas
        """
        _logger.info("[Blueprint][Formula] Creando nuevas fórmulas.")
        _logger.debug(
            "[Blueprint][Formula] Datos recibidos en create: %s",
            vals_list,
        )
        return super().create(vals_list)

    def write(self, vals):
        """
        Sobrescritura de write para registrar en log las modificaciones.

        Detalles:
          - Para cada registro afectado, muestra el nombre de la fórmula
            (si está disponible) y los valores escritos.
        """
        for rec in self:
            _logger.info(
                "[Blueprint][Formula] Modificando fórmula '%s'.",
                rec.name.name if rec.name else "-",
            )
            _logger.debug("[Blueprint][Formula] Valores en write: %s", vals)
        return super().write(vals)

    def unlink(self):
        """
        Sobrescritura de unlink para registrar en log las eliminaciones.

        Al borrar una fórmula:
          - Se deja rastro del nombre y del plano al que pertenecía.
        """
        for rec in self:
            _logger.warning(
                "[Blueprint][Formula] Eliminando fórmula '%s' del plano ID %s",
                rec.name.name if rec.name else "-",
                rec.blueprint_id.id,
            )
        return super().unlink()

    # -------------------------------------------------------------------------
    # Restricciones SQL
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            # Evita que el mismo nombre de fórmula (etiqueta del SVG) se use
            # más de una vez dentro del mismo plano. Cada etiqueta detectada
            # debe tener, como máximo, una única fórmula asociada en un plano.
            "unique_formula_per_blueprint",
            "unique(name, blueprint_id)",
            ("Ya existe una fórmula configurada para esta etiqueta " "en este plano."),
        ),
    ]
