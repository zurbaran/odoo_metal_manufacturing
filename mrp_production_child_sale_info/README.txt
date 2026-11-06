Propagación de ventas a fabricación — Odoo 19 CE
================================================================================

Conserva la línea de venta de la OF padre al preparar el aprovisionamiento
MTO de sus componentes, tanto fabricados como comprados. ``sale_mrp`` copia
nativamente ese valor a la OF hija. No se sobrescribe ``_prepare_mo_vals``.

Odoo 19 usa ``stock.reference`` y no ``procurement.group``. Al crear una OF
con línea de venta, se vincula su pedido a ``reference_ids.sale_ids`` sin
reemplazar las ventas ya presentes. Las OF sin venta mantienen su flujo nativo.

Odoo 18 copiaba ``sale_line_id`` a la línea de compra desde el aprovisionamiento.
Odoo 19 lo restringe al dropshipping. El módulo restaura esa copia para los
componentes de OF vinculadas a ventas mediante una marca específica en sus
valores de aprovisionamiento. Mantiene separadas las compras de componentes
de distintas líneas de venta, tanto al agrupar aprovisionamientos como al
buscar líneas de compra existentes. Las compras MTO ordinarias no reciben
esa marca y conservan su comportamiento nativo.

La recepción de materias primas conserva la semántica de Odoo 19 y no cuenta
como entrega del producto terminado vendido. Una prueba real confirma ventas,
OF padre/hija y compras, incluyendo varias ventas del mismo componente.

No atribuye una venta a componentes repuestos por stock/MTS: si se agrupan
necesidades de varias ventas no hay correspondencia exclusiva garantizada.
