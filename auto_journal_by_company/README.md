# Auto Journal by Company — Odoo 19

Mantiene un diario compatible al cambiar la compañía o el tipo de factura en
el formulario. Conserva los diarios manuales válidos y utiliza el selector
nativo de Odoo 19, que contempla moneda, tipo de documento y sucursales.

La creación de facturas se deja al núcleo. No se sobrescribe `create`.
Se mantiene `_auto_assign_journal` y el onchange: al cambiar la compañía de
una factura en borrador, el núcleo revisado puede conservar el diario de la
compañía anterior. Una prueba con el formulario real reproduce ese caso.

Las pruebas incluyen facturas de cliente/proveedor, abonos, selección manual,
compañía explícita diferente de la activa y cambio de compañía en formulario.
