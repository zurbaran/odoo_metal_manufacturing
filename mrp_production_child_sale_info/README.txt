Propagación de ventas a fabricación — Odoo 19 CE
================================================================================

Conserva la línea de venta de la OF padre al preparar el aprovisionamiento
MTO de sus componentes, tanto fabricados como comprados. ``sale_mrp`` copia
nativamente ese valor a la OF hija y ``sale_purchase_stock`` lo usa en compras.
El módulo no vuelve a sobrescribir ``stock.rule._prepare_mo_vals``.

Odoo 19 usa ``stock.reference`` y no ``procurement.group``. Al crear una OF
con línea de venta, se vincula su pedido a ``reference_ids.sale_ids`` sin
reemplazar las ventas ya presentes. Las OF sin venta mantienen su flujo nativo.

No atribuye una venta a componentes repuestos por stock/MTS: si se agrupan
necesidades de varias ventas no hay correspondencia exclusiva garantizada.
