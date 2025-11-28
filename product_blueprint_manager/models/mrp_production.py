import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_print_blueprint_mrp(self):
        """
        Lanza la impresión del plano de fabricación desde la Orden de Fabricación.

        - Localiza el/los pedidos de venta relacionados con esta MO.
        - Reutiliza la acción `action_print_blueprint` del `sale.order`,
          para generar exactamente el mismo plano que desde el presupuesto.
        """
        self.ensure_one()

        # 1) Intentar encontrar pedidos de venta a través de los movimientos destino
        sale_orders = self.mapped("move_dest_ids.sale_line_id.order_id")

        # 2) Fallback: a través del procurement group (sale_mrp suele rellenar sale_id)
        if not sale_orders and getattr(self, "procurement_group_id", False):
            sale_orders = self.procurement_group_id.sale_id

        if not sale_orders:
            # No hay ninguna venta asociada: no podemos saber mmA, mmB, custom, etc.
            raise UserError(
                _(
                    "No se ha encontrado ningún pedido de venta relacionado "
                    "para esta Orden de Fabricación.\n"
                    "No es posible generar el plano de fabricación."
                )
            )

        # Normalmente será 1:1 MO ↔ Pedido de Venta
        sale_order = sale_orders[0]
        _logger.info(
            "[Blueprint][MRP] Lanzando impresión de plano de fabricación desde MO %s "
            "usando pedido de venta %s",
            self.name,
            sale_order.name,
        )

        # Reutilizamos la acción existente del presupuesto
        if not hasattr(sale_order, "action_print_blueprint"):
            raise UserError(
                _(
                    "El pedido de venta asociado no dispone de la acción "
                    "`action_print_blueprint`. ¿Está instalado y cargado el "
                    "módulo de planos de fabricación?"
                )
            )

        return sale_order.action_print_blueprint()
