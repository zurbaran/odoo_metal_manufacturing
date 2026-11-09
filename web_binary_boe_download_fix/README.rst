Binary download fix for AEAT BOE exports — Odoo 19
================================================================================

Módulo de compatibilidad sin parche JavaScript. No instalar en bases nuevas.
Actualizar en bases existentes para retirar el parche de los activos web.

Odoo 19 ya utiliza ``download({url: "/web/content", data: ...})`` en
``BinaryField.onFileDownload``, enviando modelo, ID, campo y nombre de archivo.
El parche anterior llamaba ``downloadFile(url)``: esa llamada es válida y
realiza un GET cuando solo se pasa la URL. La explicación anterior que lo
calificaba como descarga del texto literal de la URL era incorrecta.

Se retira por equivalencia verificada del componente nativo para un asistente
BOE guardado: la prueba de navegador ejecuta ``BinaryField.onFileDownload``
con tamaño binario y base64, comprueba el POST y verifica bytes y nombre. La
misma prueba comprueba que ``downloadFile(url)`` realiza un GET correcto.

No se ha demostrado que exista el fallo original en Odoo 19. Si aparece un
problema de descarga, debe reproducirse sobre el comportamiento nativo antes
de añadir otro parche.
