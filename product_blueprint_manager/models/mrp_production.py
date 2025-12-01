import logging  # Módulo estándar de Python para registro de logs

from odoo import _, models  # '_' para traducciones, 'models' para definir modelos Odoo
from odoo.exceptions import (
    UserError,  # Excepción controlada para mostrar errores al usuario
)

_logger = logging.getLogger(__name__)  # Logger específico de este módulo


class MrpProduction(models.Model):
    # Extiende el modelo nativo 'mrp.production' para añadir
    #  lógica relacionada con planos
    _inherit = "mrp.production"

    def action_print_blueprint_mrp(self):
        """
        Lanza la impresión del plano de fabricación desde la Orden de Fabricación.

        - Localiza el/los pedidos de venta relacionados con esta MO.
        - Reutiliza la acción `action_print_blueprint` del `sale.order`,
          para generar exactamente el mismo plano que desde el presupuesto.
        """
        # Asegura que el método se llama sobre un único registro (una sola MO)
        self.ensure_one()

        # 1) Intentar encontrar pedidos de venta a través de los movimientos destino
        #    Recorre los movimientos destino (move_dest_ids) y de ahí llega a
        #    la línea de venta (sale_line_id) y finalmente al pedido (order_id).
        sale_orders = self.mapped("move_dest_ids.sale_line_id.order_id")

        # 2) Fallback: a través del procurement group (sale_mrp suele rellenar sale_id)
        #    Si no se han encontrado pedidos vía movimientos, intenta usar el grupo
        #    de aprovisionamiento, que a menudo guarda la relación con sale.order.
        if not sale_orders and getattr(self, "procurement_group_id", False):
            sale_orders = self.procurement_group_id.sale_id

        if not sale_orders:
            # No hay ninguna venta asociada: no podemos saber mmA, mmB, custom, etc.
            # Se lanza un error amigable para el usuario indicando el motivo.
            raise UserError(
                _(
                    "No se ha encontrado ningún pedido de venta relacionado "
                    "para esta Orden de Fabricación.\n"
                    "No es posible generar el plano de fabricación."
                )
            )

        # Normalmente será 1:1 MO ↔ Pedido de Venta
        # En caso de múltiples ventas, se toma la primera por convención.
        sale_order = sale_orders[0]
        _logger.info(
            "[Blueprint][MRP] Lanzando impresión de plano de fabricación desde MO %s "
            "usando pedido de venta %s",
            self.name,
            sale_order.name,
        )

        # Reutilizamos la acción existente del presupuesto
        # Comprobamos que el pedido de venta tiene el método esperado
        # (proporcionado por el módulo 'product_blueprint_manager').
        if not hasattr(sale_order, "action_print_blueprint"):
            raise UserError(
                _(
                    "El pedido de venta asociado no dispone de la acción "
                    "`action_print_blueprint`. ¿Está instalado y cargado el "
                    "módulo de planos de fabricación?"
                )
            )

        # Delegamos en la acción del sale.order para generar y devolver el reporte PDF
        return sale_order.action_print_blueprint()
