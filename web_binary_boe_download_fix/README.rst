Binary download fix for AEAT BOE exports — Odoo 19
================================================================================

Módulo de compatibilidad sin parche JavaScript. No instalar en bases nuevas.
Actualizar en bases existentes para retirar el parche de los activos web.

Odoo 19 ya utiliza ``download({url: "/web/content", data: ...})`` en
``BinaryField.onFileDownload``, enviando modelo, ID, campo y nombre de archivo.
El parche anterior llamaba ``downloadFile(url)``, que crea un archivo local
con el texto recibido y no descarga una URL.

No se ha demostrado que exista el fallo original en Odoo 19. Si aparece un
problema de descarga, debe reproducirse sobre el comportamiento nativo antes
de añadir otro parche.
