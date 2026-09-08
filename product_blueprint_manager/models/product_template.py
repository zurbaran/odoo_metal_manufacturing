import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

# Se obtiene un logger específico para este módulo. Permite trazar
# la actividad relacionada con la gestión de planos y fórmulas
# desde el modelo product.template.
_logger = logging.getLogger(__name__)

_BLUEPRINT_USER_GROUP = "product_blueprint_manager.group_product_blueprint_user"


class ProductTemplate(models.Model):
    """Extensión del modelo product.template para agregar
    la gestión de planos y fórmulas.

    Este modelo hereda de ``product.template`` y añade:

    - Un conjunto de planos (``blueprint_ids``) asociados a la plantilla de producto.
    - Un conjunto de fórmulas (``formula_ids``) que se aplican a dichos planos.
    - Un campo computado (``attribute_ids``) que expone los atributos
      configurados en la plantilla de producto.

    El objetivo principal es centralizar, a nivel de plantilla, la relación entre:
    producto ↔ planos SVG ↔ fórmulas (para cálculos dimensionados o similares).
    """

    _inherit = "product.template"

    # Conjunto de planos asociados a la plantilla de producto.
    # Cada plano contiene un SVG con fórmulas que se evaluarán en función
    # de los atributos y valores personalizados de las líneas de venta.
    blueprint_ids = fields.One2many(
        "product.blueprint",
        "product_id",
        string="Planos",
        groups=_BLUEPRINT_USER_GROUP,
    )

    # Conjunto de fórmulas ligadas a la plantilla de producto. Estas fórmulas
    # referencian nombres de variables presentes en el SVG y se evaluarán
    # utilizando los valores de atributos (custom y estándar) de las líneas
    # de venta que referencien este producto.
    formula_ids = fields.One2many(
        "product.blueprint.formula",
        "product_id",
        string="Fórmulas",
        groups=_BLUEPRINT_USER_GROUP,
    )

    # Campo auxiliar que expone, de forma computada, los atributos de la
    # plantilla de producto. No se almacena en base de datos y se utiliza
    # como apoyo en vistas o lógica donde conviene tener el listado de
    # atributos directamente sobre product.template.
    attribute_ids = fields.Many2many(
        comodel_name="product.attribute",
        compute="_compute_attribute_ids",
        store=False,
    )

    def _check_blueprint_user_access(self):
        """Exige acceso explícito a planos para los helpers públicos."""
        if not self.env.user.has_group(_BLUEPRINT_USER_GROUP):
            raise AccessError(_("No tiene permisos para acceder a planos de producto."))

    def get_custom_attribute_values(self, sale_order_line=None):
        """
        Obtiene los valores de atributos personalizados para una línea de
        pedido de venta dada.

        Esta función es un helper que delega en el campo técnico
        ``blueprint_custom_values`` de la propia línea de venta, el cual
        ya contiene la representación serializada (str) de las variables
        que intervienen en las fórmulas del plano.

        Args:
            sale_order_line (recordset): La línea de pedido de venta. Si
                es ``None``, no se puede determinar información de atributos.

        Returns:
            dict o str: Un diccionario (o representación en texto) de valores
            de atributos personalizados utilizados en las fórmulas del blueprint.
            En la implementación actual, devuelve el contenido de
            ``sale_order_line.blueprint_custom_values`` tal cual, o un
            valor vacío si no se proporcionó la línea.
        """
        self._check_blueprint_user_access()
        _logger.debug(
            "[Blueprint] Obteniendo valores de atributos personalizados "
            f"para {self.name}, Linea de venta: "
            f"{sale_order_line.id if sale_order_line else 'Ninguna'}"
        )
        # Si no se pasa línea de venta, se devuelve un valor vacío.
        # En caso contrario, se devuelve el contenido del campo técnico
        # blueprint_custom_values calculado en sale.order.line.
        return sale_order_line.blueprint_custom_values if sale_order_line else {}

    # Eliminamos los metodos relacionados con la previsualizacion
    # def action_generate_blueprint_preview(self):
    #     """
    #     Genera una previsualización del primer plano asociado al producto.
    #     Acción para usar en un botón.
    #     """
    #     return self.generate_blueprint_report(mode="preview")

    # def generate_blueprint_report(
    #     self, sale_order_line=None, mode="preview"
    # ):
    def generate_blueprint_report(self, sale_order_line=None):
        """
        Genera un reporte de blueprint.

        Esta función se utiliza, principalmente, como punto de entrada
        para lanzar un informe de planos asociado al pedido de venta que
        contiene la línea proporcionada.

        Args:
            sale_order_line (recordset, optional):
                La línea de pedido de venta para el reporte final.
                Debe ser una instancia de ``sale.order.line`` que
                apunte a este ``product.template``. Defaults to None.

        Returns:
            dict or bool: La acción del reporte (diccionario devuelto por
            ``ir.actions.report``) o False si hay un error o la línea no
            se proporciona.

        Flujo:
            1. Verifica que el registro actual sea único (``ensure_one()``).
            2. Comprueba que se haya pasado una línea de venta. Si falta,
               registra un error en el log y devuelve ``False``.
            3. Localiza el reporte vía ``_get_report_from_name`` usando el
               nombre técnico del informe definido en los datos XML.
            4. Llama a ``report_action`` sobre el pedido de venta asociado
               a la línea (``sale_order_line.order_id``), devolviendo la
               acción estándar de Odoo para la impresión del PDF/HTML.
        """
        self.ensure_one()
        self._check_blueprint_user_access()

        if not sale_order_line:
            _logger.error("Sale order line is required for generating the blueprint.")
            return False

        _logger.info(
            "Generando reporte de blueprint para el producto "
            f"{self.name} (SO line ID: {sale_order_line.id})"
        )

        # Se recupera la acción de informe definida en los datos del módulo
        # (product_blueprint_manager.action_report_sale_order_blueprint).
        report_action = self.env["ir.actions.report"]._get_report_from_name(
            "product_blueprint_manager.action_report_sale_order_blueprint"
        )
        # Se devuelve la acción del reporte aplicada al pedido de venta
        # correspondiente a la línea proporcionada.
        return report_action.report_action(sale_order_line.order_id)

    @api.depends("attribute_line_ids")
    def _compute_attribute_ids(self):
        """
        Computa el campo ``attribute_ids`` a partir de las líneas de atributos
        de la plantilla de producto.

        Para cada ``product.template``:
            - Recorre sus ``attribute_line_ids``.
            - Mapea dichas líneas a sus ``attribute_id``.
            - Asigna el conjunto resultante al campo Many2many ``attribute_ids``.

        Este método NO almacena los datos en base de datos (``store=False``),
        por lo que se recalcula cuando cambian las líneas de atributo.
        """
        for product in self:
            # attribute_line_ids.mapped("attribute_id") devuelve el conjunto
            # de atributos configurados en la plantilla. Esto permite tener
            # un acceso directo a los atributos desde el propio product.template.
            product.attribute_ids = product.attribute_line_ids.mapped("attribute_id")
