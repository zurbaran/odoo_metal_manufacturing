# Módulo de extensión del modelo `sale.order` para añadir acciones
# específicas de impresión de planos de fabricación y compra, así
# como controlar el nombre base de los ficheros generados.

import logging

from odoo import models

# Logger para trazar la ejecución de las acciones relacionadas con blueprints
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Extensión del modelo sale.order para la impresión del
    reporte de blueprints.

    Este modelo añade:
      - Botones/acciones para imprimir planos de fabricación.
      - Botones/acciones para imprimir planos de compra.
      - Lógica para personalizar el nombre del archivo PDF resultante
        cuando se imprimen estos reportes de planos.
    """

    _inherit = "sale.order"

    def action_print_blueprint(self):
        """
        Acción para imprimir el reporte de blueprints.
        Para usar en un botón.

        Flujo:
          1. `ensure_one()` garantiza que la acción se ejecute sobre un único
             registro de pedido de venta.
          2. Se escribe una traza de depuración en el log.
          3. Se localiza la acción de informe definida en `ir.actions.report`
             con el XML-ID
             `product_blueprint_manager.action_report_sale_order_blueprint`.
          4. Se llama a `report_action(self)` para generar el PDF asociado,
             usando el propio pedido (`self`) como documento.
        """
        self.ensure_one()
        _logger.debug(
            "[Blueprint] Acción ejecutada: impresión de blueprints de "
            f"fabricación para el pedido: {self.name}"
        )

        # `env.ref()` recupera el registro de `ir.actions.report` por su XML-ID.
        # `report_action(self)` genera y devuelve la acción que Odoo utilizará
        # para construir el informe (PDF/HTML) en el cliente.
        return self.env.ref(
            "product_blueprint_manager.action_report_sale_order_blueprint"
        ).report_action(self)

    def action_print_purchase_blueprint(self):
        """
        Acción para imprimir el reporte de planos asociados a órdenes de compra.

        Aunque el modelo de informe está ligado a `sale.order`, este método
        genera un reporte pensado para el proveedor (plano de compra) en base
        a las líneas del propio pedido de venta.

        Flujo:
          1. `ensure_one()` asegura que solo se procese un pedido.
          2. Se registra en el log la ejecución de la acción.
          3. Se recupera la acción de informe específica para planos de compra.
          4. Se llama a `report_action(self)` para generar el documento.
        """
        self.ensure_one()
        _logger.debug(
            "[Blueprint] Acción ejecutada: impresión de blueprints de "
            f"compra para el pedido: {self.name}"
        )
        return self.env.ref(
            "product_blueprint_manager.action_report_purchase_order_blueprint"
        ).report_action(self)

    def _get_report_base_filename(self):
        """
        Sobreescribe el nombre base del reporte para el nuevo informe de
        blueprints.

        Esta función es llamada internamente por el motor de informes para
        determinar el nombre base del archivo generado (antes de añadir
        extensiones, sufijos de descarga, etc.).

        Lógica aplicada:
          - Solo se personaliza el nombre cuando el modelo activo es
            `sale.order` y el registro activo coincide con `self.id`.
          - Se consulta el contexto (`self.env.context`) para obtener el
            identificador del reporte (`report`), que Odoo establece cuando
            está generando un informe concreto.
          - Si el reporte es:
              * `product_blueprint_manager.report_sale_order_blueprint_document`
                → nombre: `Plano_Fabricacion_<nombre_pedido>`
              * `product_blueprint_manager.report_purchase_order_blueprint_document`
                → nombre: `Plano_Compra_<nombre_pedido>`
          - En cualquier otro caso, se delega en la implementación estándar
            llamando a `super()._get_report_base_filename()`.

        Returns:
            str: El nombre base del reporte.
        """
        self.ensure_one()
        if (
            self.env.context.get("active_model") == "sale.order"
            and self.env.context.get("active_id") == self.id
        ):
            # El contexto `report` contiene el nombre técnico del informe
            # (`report_name` definido en `ir.actions.report`).
            report = self.env.context.get("report")
            if report == (
                "product_blueprint_manager.report_" "sale_order_blueprint_document"
            ):
                _logger.debug(
                    "[Blueprint] Generando nombre de archivo para "
                    "reporte de "
                    f"fabricación: Plano_Fabricacion_{self.name}"
                )
                return f"Plano_Fabricacion_{self.name}"
            elif report == (
                "product_blueprint_manager.report_" "purchase_order_blueprint_document"
            ):
                _logger.debug(
                    "[Blueprint] Generando nombre de archivo para "
                    "reporte de "
                    f"compra: Plano_Compra_{self.name}"
                )
                return f"Plano_Compra_{self.name}"
        # Si no se cumplen las condiciones (otro modelo, otro informe, etc.)
        # se llama al comportamiento estándar del modelo padre.
        return super()._get_report_base_filename()
