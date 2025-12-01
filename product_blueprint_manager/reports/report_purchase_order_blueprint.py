import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ReportPurchaseOrderBlueprint(models.AbstractModel):
    """Backend del informe QWeb de planos de compra.

    Este modelo abstracto se enlaza con la plantilla QWeb
    ``product_blueprint_manager.report_purchase_order_blueprint`` mediante
    el campo ``report_name`` definido en el registro ``ir.actions.report``.

    Su responsabilidad principal es:
      * Recibir los ``docids`` (IDs de ``sale.order``) que se van a imprimir.
      * Forzar la evaluación y generación de los planos de tipo *compra*
        para todas las líneas de esos pedidos.
      * Devolver al motor de informes la estructura estándar con los
        documentos a renderizar.
    """

    _name = "report.product_blueprint_manager.report_purchase_order_blueprint"
    _description = "Generador de planos para orden de compra"

    def _get_report_values(self, docids, data=None):
        """Construye el diccionario de datos que consumirá el informe QWeb.

        Parámetros
        ----------
        docids : list[int]
            Lista de identificadores de los registros de ``sale.order`` que
            se quieren imprimir.
        data : dict | None
            Datos adicionales opcionales pasados desde la acción de informe.
            En este caso no se usan, por lo que se deja con el valor por
            defecto ``None``.

        Flujo
        -----
        1. Se buscan los pedidos de venta a partir de ``docids``.
        2. Para cada pedido:
           * Se recorre cada línea de pedido.
           * Se llama a ``_get_evaluated_blueprint(type_blueprint='purchase')``
             para que la línea:
               - aplique las condiciones de atributos,
               - evalúe las fórmulas definidas,
               - genere los adjuntos SVG/PNG,
               - deje los planos listos para ser consumidos por la plantilla.
        3. Se devuelve el diccionario estándar con:
           * ``doc_ids``   → lista de IDs recibidos.
           * ``doc_model`` → nombre técnico del modelo (``sale.order``).
           * ``docs``      → recordset de pedidos a iterar en la QWeb.

        Returns
        -------
        dict
            Estructura compatible con el motor de informes de Odoo.
        """
        # Obtenemos los pedidos que se van a imprimir a partir de los IDs
        # que recibe el informe (normalmente, uno o varios sale.order).
        orders = self.env["sale.order"].browse(docids)

        # Recorremos cada pedido y preparamos sus planos de compra.
        for order in orders:
            _logger.debug(f"[Blueprint][Purchase] Procesando orden {order.name}")
            for line in order.order_line:
                _logger.debug(
                    f"[Blueprint][Purchase] Línea {line.id} - Producto:\
                          {line.product_id.name}"
                )
                # Para cada línea del pedido generamos/evaluamos sus planos
                # tipo "purchase". Esto deja los adjuntos preparados para que
                # la plantilla QWeb sólo tenga que mostrarlos.
                line._get_evaluated_blueprint(type_blueprint="purchase")

        # Devolvemos la estructura estándar que la plantilla QWeb espera.
        return {
            "doc_ids": docids,
            "doc_model": "sale.order",
            "docs": orders,
        }
