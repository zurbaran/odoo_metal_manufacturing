"""Módulo de integración del reporte de planos de venta.

Este módulo define un modelo abstracto de reporte que se encarga de:
- Localizar los pedidos de venta (`sale.order`) a partir de `docids`.
- Forzar la generación/evaluación previa de todos los planos asociados
  a las líneas de pedido mediante `_get_evaluated_blueprint()`.
- Devolver la estructura estándar requerida por los reportes QWeb de Odoo.
"""

import logging

from odoo import models

# Logger específico para este módulo. Permite trazar el proceso de
# generación de planos antes de lanzar el reporte QWeb.
_logger = logging.getLogger(__name__)


class ReportBlueprintAutoGenerate(models.AbstractModel):
    """Modelo abstracto de reporte para planos de pedido de venta.

    Este modelo se vincula al reporte QWeb
    `product_blueprint_manager.report_sale_order_blueprint` y su cometido
    principal es asegurarse de que, antes de renderizar el PDF/HTML, todos
    los planos asociados a cada línea de venta ya han sido generados y
    adjuntados como ficheros (SVG/PNG) mediante la lógica existente en
    `sale.order.line._get_evaluated_blueprint()`.

    Atributos de clase:
        _name (str): Nombre técnico del modelo de reporte, usado por Odoo
            para resolver el reporte desde `ir.actions.report`.
        _description (str): Descripción legible del propósito del modelo.
    """

    _name = "report.product_blueprint_manager.report_sale_order_blueprint"
    _description = "Generador automático de planos evaluados antes del reporte"

    def _get_report_values(self, docids, data=None):
        """Construye el diccionario de valores que usará el QWeb del reporte.

        Antes de devolver los `docs`, recorre todos los pedidos y líneas
        para forzar la evaluación y generación de los planos, de forma que:

          - Se calculen todas las fórmulas definidas en los blueprints.
          - Se generen y vinculen los adjuntos SVG/PNG necesarios para el PDF.
          - El reporte QWeb pueda limitarse a mostrar los adjuntos ya evaluados.

        Args:
            docids (list[int]): Lista de IDs de `sale.order` para los que se
                va a generar el reporte.
            data (dict | None): Diccionario de datos adicionales que pueden
                ser pasados desde la acción del reporte. No se usa en esta
                implementación, pero se mantiene por compatibilidad con la
                firma estándar de Odoo.

        Returns:
            dict: Estructura con las claves:
                - ``doc_ids``: Lista de IDs de los documentos.
                - ``doc_model``: Nombre del modelo principal (`sale.order`).
                - ``docs``: Recordset de pedidos que se iterará en la plantilla.
        """
        # Obtenemos los pedidos de venta a partir de los IDs recibidos.
        orders = self.env["sale.order"].browse(docids)

        # Recorremos cada pedido de venta.
        for order in orders:
            _logger.debug(f"[Blueprint][Auto] Procesando orden {order.name}")

            # Para cada línea de pedido, solicitamos la generación/evaluación
            # de sus planos. Esto puede crear o actualizar adjuntos vinculados
            # a la línea, que posteriormente serán usados en el QWeb.
            for line in order.order_line:
                _logger.debug(
                    f"[Blueprint][Auto] Línea {line.id} - Producto:\
                          {line.product_id.name}"
                )
                # Llama al método que se encarga de:
                # - Filtrar blueprints aplicables según tipo de plano.
                # - Evaluar fórmulas.
                # - Generar SVG/PNG y adjuntarlos a la línea.
                line._get_evaluated_blueprint()

        # Devolvemos la estructura estándar que espera el motor de reportes
        # de Odoo para construir el contexto del QWeb.
        return {
            "doc_ids": docids,
            "doc_model": "sale.order",
            "docs": orders,
        }
