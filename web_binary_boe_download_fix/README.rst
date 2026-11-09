Binary download fix for AEAT BOE exports — 18.0
================================================================================

Estado: INNECESARIO en las revisiones actualizadas comprobadas
-------------------------------------------------------------

El 9 de noviembre de 2026 se ha comprobado Odoo 18 CE y OCA 18.0
sin instalar este módulo: exportación real del modelo 130, botón Exportar y
descarga desde el campo binario del asistente BOE, con contenido y nombre
correctos. No es necesario instalarlo en nuevos despliegues actualizados.

Se conserva el parche original por compatibilidad con instalaciones antiguas.
Esta marca no lo desactiva ni desinstala automáticamente.

Antes de retirarlo de una instalación existente, comprobar su versión de
Odoo/OCA y el flujo de descarga sin el parche en una copia. No se da por
resuelto el fallo de instalaciones antiguas o personalizadas sin comprobarlas.

La generación del archivo corresponde a OCA; la descarga del campo binario
la realiza Odoo mediante POST a /web/content. Tu parche fuerza una URL GET
para el modelo l10n.es.aeat.report.export_to_boe y el campo data. Ese GET es
válido; no hay evidencia de que el parche estuviese roto por usarlo.

OCA corrigió además la carga del nombre del archivo en el asistente BOE.
Ese problema relacionado no demuestra por sí solo la causa del antiguo 404.

Consultar VALIDATION.md para los resultados de ambas versiones, revisiones
exactas, historial y prueba de navegador reproducible. La declaración usada
es sintética; esta comprobación no valida el cálculo fiscal del modelo.

Autor: Antonio Caballero. Licencia AGPL-3.
