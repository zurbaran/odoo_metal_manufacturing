import logging

from odoo import api, fields, models

# Logger del módulo para trazar operaciones sobre las etiquetas de fórmulas
_logger = logging.getLogger(__name__)


class ProductBlueprintFormulaName(models.Model):
    """
    Modelo que almacena los nombres/etiquetas de fórmulas detectadas en un SVG.

    Cada registro representa una etiqueta concreta de fórmula en un plano SVG:
      - `name`: Nombre lógico de la fórmula (por ejemplo, LENGTH, mmA, mmB...).
      - `blueprint_id`: Plano al que pertenece la etiqueta.
      - `svg_element_id`: ID del nodo SVG concreto donde se encontró.
      - `fill_color` y `font_size`: Estilo visual detectado para esa fórmula.

    Este modelo se alimenta automáticamente durante el análisis del SVG, y
    posteriormente se usa como referencia al configurar las fórmulas de precio/
    medida en `product.blueprint.formula`.
    """

    _name = "product.blueprint.formula.name"
    _description = "Nombre de Etiqueta de Fórmula"
    # Orden por defecto al listar etiquetas (útil en vistas many2one/m2m)
    _order = "name asc"

    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------

    name = fields.Char(
        string="Nombre de la Etiqueta",
        required=True,
        help="Nombre de la etiqueta detectada en el plano SVG.",
    )
    blueprint_id = fields.Many2one(
        "product.blueprint",
        string="Plano Asociado",
        required=True,
        ondelete="cascade",
        help=(
            "Plano SVG en el que se ha detectado esta etiqueta de fórmula. "
            "Si el plano se elimina, las etiquetas asociadas también se "
            "eliminan."
        ),
    )
    # Valores visuales detectados en el nodo SVG. Se usan como valores por
    # defecto al crear la fórmula asociada, y se pueden ajustar manualmente.
    fill_color = fields.Char(
        string="Color del Texto",
        default="#000000",
        help=(
            "Color de relleno del texto asociado a esta fórmula en el SVG. "
            "Se detecta automáticamente, pero puede ser modificado."
        ),
    )
    font_size = fields.Char(
        string="Tamaño de Fuente",
        default="12px",
        help=(
            "Tamaño de fuente del texto asociado a esta fórmula en el SVG. "
            "Se detecta automáticamente en el análisis del plano."
        ),
    )
    svg_element_id = fields.Char(
        string="ID de nodo SVG",
        help="ID del elemento SVG que contiene esta fórmula.",
    )

    # -------------------------------------------------------------------------
    # Restricciones de integridad (API Odoo 19)
    # -------------------------------------------------------------------------

    _unique_formula_per_node = models.Constraint(
        "UNIQUE (name, blueprint_id, svg_element_id)",
        "Cada fórmula debe ser única por ID SVG dentro del mismo plano.",
    )

    # -------------------------------------------------------------------------
    # Overrides de create/write/unlink para logging detallado
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrecarga de create para registrar en el log la creación de etiquetas.

        Se limita a hacer logging y delega la lógica de negocio al create
        original de Odoo.
        """
        for vals in vals_list:
            _logger.debug(
                "[Blueprint][Formula Name] Creando nueva etiqueta: '"
                f"{vals.get('name')}' "
                f"para plano ID: {vals.get('blueprint_id')} "
                f"con color={vals.get('fill_color')} "
                f"tamaño={vals.get('font_size')} - "
                f"Nodo SVG ID={vals.get('svg_element_id')}"
            )
        return super().create(vals_list)

    def write(self, vals):
        """
        Sobrecarga de write para registrar modificaciones sobre las etiquetas.

        No altera la lógica de actualización; únicamente añade trazas de debug
        antes de delegar en el write estándar de Odoo.
        """
        for record in self:
            _logger.debug(
                "[Blueprint][Formula Name] Modificando etiqueta '"
                f"{record.name}' del plano ID {record.blueprint_id.id} "
                f"con cambios: {vals}"
            )
        return super().write(vals)

    def unlink(self):
        """
        Sobrecarga de unlink para registrar qué etiquetas se eliminan.

        Permite seguir desde el log qué etiquetas de fórmula se están
        limpiando, especialmente útil cuando se reimportan o se rehacen planos.
        """
        for record in self:
            _logger.warning(
                "[Blueprint][Formula Name] Eliminando etiqueta '"
                f"{record.name}' del plano ID {record.blueprint_id.id} "
                f"(Nodo SVG ID={record.svg_element_id})."
            )
        return super().unlink()

    # -------------------------------------------------------------------------
    # Búsquedas y utilidades
    # -------------------------------------------------------------------------

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """
        Filtra la búsqueda de etiquetas en función del plano indicado en contexto.

        Si en el contexto viene `blueprint_id`, solo se buscan etiquetas
        pertenecientes a ese plano. Esto hace que, al seleccionar una etiqueta
        desde la configuración de fórmulas, solo aparezcan las relevantes.
        """
        args = args or []
        blueprint_id = self.env.context.get("blueprint_id")
        if blueprint_id:
            args += [("blueprint_id", "=", blueprint_id)]
        return super().name_search(name, args, operator=operator, limit=limit)

    def _safe_evaluate_formula(self, expression, variables):
        """
        Helper para evaluar una fórmula utilizando la implementación probada
        en `sale.order.line.safe_evaluate_formula`.

        Este método no implementa la lógica de evaluación por sí mismo, sino
        que delega a la versión del modelo de línea de venta, que ya está
        testeada y centraliza el comportamiento de seguridad (whitelist de
        funciones, entornos limitados, etc.).

        :param expression: Cadena con la expresión a evaluar, p.e. 'mmA * 2'.
        :param variables: Diccionario con las variables disponibles.
        :return: Resultado en formato string o 'Error' si la evaluación falla.
        """
        # reusa la implementación probada de la línea de venta
        return self.env["sale.order.line"].safe_evaluate_formula(expression, variables)
