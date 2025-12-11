========================================
Binary download fix for AEAT BOE exports
========================================

Objetivo
========

Este módulo corrige un problema de descarga de ficheros generados por
wizards (como los de ``l10n_es_aeat``) en Odoo 18 Community.

En ciertos casos, el botón de descarga de un campo binario en modo
sólo lectura dispara una petición ``GET /web/content/`` sin parámetros,
lo que provoca un error 404 y el típico mensaje en la interfaz:

*RPC_ERROR: Arbitrary Uncaught Python Exception*

Causa
=====

En Odoo 18, el componente ``BinaryField`` usa un helper de descarga
basado en ``/web/content`` que, en algunos escenarios (como el wizard
``l10n.es.aeat.report.export_to_boe``), no envía correctamente los
parámetros necesarios en la petición, dando lugar a un 404.
corrige un bug introducido en el archivo:
addons/web/static/src/views/fields/binary/binary_field.js

Solución
========

Este módulo aplica un *patch* al componente ``BinaryField`` de ``web``
para que, al descargar, construya explícitamente la URL REST:

``/web/content/<model>/<id>/<field>/<filename>?download=true``

y utilice ``downloadFile._download(url)`` para realizar la descarga.

De esta forma:

- Se evita el ``GET /web/content/`` vacío (404).
- Se aprovecha la ruta REST estándar ya implementada en el core de Odoo.
- No se modifica ningún archivo del core, sólo se parchea el comportamiento
  del campo binario mediante JavaScript.

