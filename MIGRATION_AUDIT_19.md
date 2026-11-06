# Revisión Odoo 18 → 19 CE (6 de noviembre de 2026)

## Alcance y referencias

Comparación de los ocho módulos de 18.0 (`4780eb1dd4d3a3049d030ca2d27d1704cd02b57b`)
con 19.0 (`11eac25f0b2bb43d5ab18efacd568108b474b577`). El único módulo ausente
era `payroll_account_employee_partner`.

Código oficial contrastado: [Odoo CE 19](https://github.com/odoo/odoo/tree/66af69fda24a7b0dc7b036bf1678b8850862c247)
y [OCA/payroll 19](https://github.com/OCA/payroll/tree/2eca6caafc74d4a592ee0ca75606b4c6e3ce75b9).
Las dependencias OCA se descargaron de sus ramas 19.0 para instalar y probar.

## Resultado por módulo

| Módulo | Valor frente a Odoo 19 CE | Resultado de la revisión |
| --- | --- | --- |
| `account_reconcile_n43_beneficiary` | Mantiene valor: identificación del beneficiario N43, exclusión de titulares y recuperación de reglas antiguas. El motor y los contactos mapeados son nativos/OCA; no se reintroduce el antiguo modelo de mapeo. | API de importación y conciliación revisada; pruebas de reglas, ambigüedades y recuperación incluidas en la ejecución. |
| `auto_journal_by_company` | Redundante para su objetivo documentado: `account.move._compute_journal_id` y `_search_default_journal` seleccionan diario por compañía y tipo. | Retiradas las sobrescrituras. Se conserva como módulo de compatibilidad para actualizar instalaciones existentes; no instalar en bases nuevas. Pruebas sobre el comportamiento nativo. |
| `mrp_production_child_sale_info` | Sigue aportando la propagación de la línea de venta del padre al aprovisionamiento de componentes. Copiarla de los valores de aprovisionamiento a la OF ya es nativo. | Corregido acceso a `procurement_group_id`, inexistente en 19.0; usa `reference_ids.sale_ids`. Eliminada sobrescritura redundante de `_prepare_mo_vals`. Añadidas pruebas de componentes/OF hijas y OF sin venta. |
| `payroll_account_employee_partner` | CE no sustituye la contabilidad de nóminas de OCA ni esta personalización española. | Recuperado desde 18.0 y adaptado parcialmente; **NO instalable** porque OCA/payroll 19.0 aún no contiene `payroll_account`. No se considera una migración terminada. |
| `product_blueprint_manager` | Gestión y generación de planos SVG/PNG con fórmulas y condiciones; no equivale a adjuntar documentos nativos a un producto. | Corregida búsqueda de venta al imprimir desde OF usando `sale_line_id.order_id` y `reference_ids.sale_ids`; añadida regresión. Revisadas vistas, permisos, fórmulas e informes mediante las pruebas existentes. |
| `product_configurator_attribute_price` | Las fórmulas sobre valores personalizados y precio acumulado no son el `price_extra` fijo nativo. | Conservado. Integración con `_reset_price_unit`/`technical_price_unit` de 19 revisada; pruebas de cálculos, descripción y seguridad existentes. |
| `ui_template_enhancements` | Personalización de marca, correos y maquetación; Odoo dispone de plantillas, pero no de estas modificaciones concretas. | Conservado; instalación verifica las referencias y XPath. La apariencia final de correos/PDF con datos reales requiere revisión visual. |
| `web_binary_boe_download_fix` | Sin necesidad demostrada en 19.0: `BinaryField` ya envía los parámetros a `/web/content` con `download`. | Retirado el parche. `downloadFile(url)` trata la URL como contenido de archivo, no como una petición HTTP. Conservado como módulo de compatibilidad sin activos; no instalar en bases nuevas. |

## Nóminas: trabajo realizado y bloqueo

Se conserva toda la personalización de 18.0. Las validaciones de fechas usan
`hr.version.contract_date_start` / `contract_date_end`; el contacto bancario
alternativo usa `primary_bank_account_id`, en vez del antiguo `bank_account_id`.
Se preservan las validaciones específicas de `ES_FORM_ALT_2026`.

Falta una implementación 19.0 de `payroll_account` con la que validar
`_get_tax_details`, `_get_partner_id`, las cuentas/impuestos de las reglas y la
creación/publicación del asiento. Cambiar únicamente la versión y marcarlo
instalable ocultaría ese bloqueo. Migrar OCA/payroll_account es un trabajo
adicional; no se ha copiado silenciosamente su versión 18.0.

## Límites de la validación

La instalación limpia y las pruebas automatizadas no certifican una migración
de una base de datos real de 18 a 19. En particular, la recuperación de mapeos
N43 depende de las columnas/tablas preservadas por OpenUpgrade y del orden de
migración de `account`: el hook del módulo se ejecuta después y no puede
corregir fallos anteriores de esa migración. Probar primero una copia de la BD.

Se ha comprobado por HTTP la descarga nativa de los bytes y nombre de un
archivo del asistente BOE. No se han ejecutado pruebas de navegador ni revisión visual de los PDF/correos,
ni una nómina contabilizada con payroll_account 19. No se certifican las reglas
legales de la estructura salarial 2026. La impresión mediante wkhtmltopdf y la
descarga BOE en navegador deben validarse con los datos/configuración reales.

## Ejecución y evidencias

La instalación de los siete módulos disponibles completó la carga de 107
módulos (incluidas dependencias). Tras corregir los datos y el momento de
ejecución de las pruebas, la actualización conjunta de los siete módulos
terminó con **85 pruebas, 0 fallos y 0 errores** (resumen de Odoo).

Las pruebas de diarios y configurador se ejecutan ahora en `post_install`:
en una actualización sobre una BD con `sale_stock` y compras ya instalados,
ejecutarlas con un registro parcial en `at_install` omitía valores por defecto
de campos obligatorios de módulos todavía no cargados (`group_rfq`,
`picking_policy`). No se elimina ninguna prueba ni se debilitan sus aserciones.
La prueba nueva de fabricación usa `stock.move` sin el campo `name`, eliminado
en Odoo 19.

Entorno: Python 3.12, PostgreSQL 16, Odoo CE 19.0. Comprobación de sintaxis de
83 archivos Python y todos los XML; Ruff sobre archivos Python revisados:
sin errores. No se ha ejecutado la batería en Odoo 18.

Reproducción con las dependencias indicadas en un `addons-path` adecuado:

```sh
odoo-bin -d audit19 -i auto_journal_by_company,mrp_production_child_sale_info,product_blueprint_manager,product_configurator_attribute_price,ui_template_enhancements,web_binary_boe_download_fix,account_reconcile_n43_beneficiary --test-tags=/auto_journal_by_company,/mrp_production_child_sale_info,/product_blueprint_manager,/product_configurator_attribute_price,/web_binary_boe_download_fix,/account_reconcile_n43_beneficiary --stop-after-init
```

Después repetir con `-u` en vez de `-i` para verificar actualización dentro de
19.0. Esto no equivale a migrar una BD 18.0 con OpenUpgrade. El workflow del
repositorio incluye ahora las pruebas nuevas de fabricación y descarga BOE.

### Revisiones de dependencias usadas

| Repositorio | SHA |
| --- | --- |
| odoo19 | `66af69fda24a7b0dc7b036bf1678b8850862c247` |
| payroll19 | `2eca6caafc74d4a592ee0ca75606b4c6e3ce75b9` |
| sale-workflow | `8a5e9df2842e28f1038137389e3c6dccea78bfe5` |
| product-attribute | `dc11b552a92ee5c394e49bc48b45d571e006393d` |
| l10n-spain | `750e3a3bb13a4f962293954579f87ad8da795aa1` |
| account-financial-reporting | `f48b4ea777c444256aa1c215ec3117d604b5feff` |
| server-ux | `af19073dc86443bad8590811649a54172a81a1ef` |
| account-reconcile | `e3d99f3dc4a61f44167ce0ce70e9a0a6ad0b7540` |
| bank-statement-import | `f22941f879c45ac2a258b2e7d88fe16a867e16d9` |
