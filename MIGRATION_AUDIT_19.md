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
| `auto_journal_by_company` | La selección inicial es nativa, pero la retirada completa del módulo perdía un caso de cambio de compañía en formulario. | Conservado un onchange mínimo con el selector nativo y respeto a diarios válidos. Eliminada la sobrescritura de `create`. Regresión del cambio de compañía reproducida y corregida. |
| `mrp_production_child_sale_info` | Sigue aportando propagación de línea de venta a componentes. Odoo 19 dejó de copiarla a compras ordinarias con movimientos destino. | Usa `reference_ids.sale_ids`, delega `_prepare_mo_vals` en `sale_mrp` y restaura `sale_line_id` para compras de componentes, separándolas por origen. Prueba real venta → OF padre/hija → compra → recepción. |
| `payroll_account_employee_partner` | CE no sustituye la contabilidad de nóminas de OCA ni esta personalización española. | Adaptado y habilitado con la dependencia del [PR OCA/payroll #269](https://github.com/OCA/payroll/pull/269), fijada al SHA `ef16a76b00462717d982b6a4f45082723255b1bf`. Pendiente de integración upstream, pero disponible para instalar y probar. |
| `product_blueprint_manager` | Gestión y generación de planos SVG/PNG con fórmulas y condiciones; no equivale a adjuntar documentos nativos a un producto. | Corregida búsqueda de venta al imprimir desde OF usando `sale_line_id.order_id` y `reference_ids.sale_ids`; añadida regresión. Revisadas vistas, permisos, fórmulas e informes mediante las pruebas existentes. |
| `product_configurator_attribute_price` | Las fórmulas sobre valores personalizados y precio acumulado no son el `price_extra` fijo nativo. | Conservado. Integración con `_reset_price_unit`/`technical_price_unit` de 19 revisada; pruebas de cálculos, descripción y seguridad existentes. |
| `ui_template_enhancements` | Personalización de marca, correos y maquetación; Odoo dispone de plantillas, pero no de estas modificaciones concretas. | Conservado; instalación verifica las referencias y XPath. La apariencia final de correos/PDF con datos reales requiere revisión visual. |
| `web_binary_boe_download_fix` | Sin necesidad demostrada en 19.0: `BinaryField` ya envía los parámetros a `/web/content` con `download`. | Retirado por equivalencia comprobada con el componente nativo en navegador (POST con base64/tamaño). `downloadFile(url)` sí es un GET válido: la explicación anterior que lo consideraba roto era incorrecta. Conservado como módulo de compatibilidad sin activos. |

## Nóminas: adaptación al PR OCA/payroll #269

La revisión inicial solo comprobó la rama oficial y omitió el PR existente.
El [PR #269](https://github.com/OCA/payroll/pull/269) sigue abierto, tiene
revisiones aprobadas y sus ejecuciones de tests y pre-commit del SHA revisado
terminaron correctamente. No está integrado todavía en la rama 19.0.

Se utiliza la revisión `ef16a76b00462717d982b6a4f45082723255b1bf` del PR,
que proporciona `payroll` y `payroll_account`. No se copia esa dependencia
en este repositorio: el workflow la descarga del SHA fijo.

Se conservan las personalizaciones de 18.0 y se adaptan al contrato/versionado
`hr.version` y a `primary_bank_account_id`. Se normalizan las etiquetas de
`_get_tax_details` y se fija la compañía de la nómina al resolver cuentas
company-dependent y contabilizar. El motor contable sigue siendo el de OCA.
Las cuentas 465 y las bases 640 sujetas a retención mantienen al empleado;
475100/476000 exigen el contacto de su registro de contribución. Para otras
cuentas se delega en el comportamiento del PR.

Las pruebas de alternancia utilizan reglas sintéticas: verifican el flujo,
las 16 reglas requeridas, las jornadas, la publicación del asiento y las
restricciones de fechas/duplicados, sin certificar importes legales.

## Límites de la validación

La instalación limpia y las pruebas automatizadas no certifican una migración
de una base de datos real de 18 a 19. En particular, la recuperación de mapeos
N43 depende de las columnas/tablas preservadas por OpenUpgrade y del orden de
migración de `account`: el hook del módulo se ejecuta después y no puede
corregir fallos anteriores de esa migración. Probar primero una copia de la BD.

Se ha comprobado por HTTP la descarga nativa de los bytes y nombre de un
archivo del asistente BOE. En la revisión del 9 de noviembre se añadió una
prueba de navegador del componente nativo de descarga. No se ha hecho revisión
visual de los PDF/correos. No se certifican las reglas legales de la estructura
salarial 2026. La impresión mediante wkhtmltopdf y la
descarga BOE en navegador deben validarse con los datos/configuración reales.

## Ejecución y evidencias

La instalación de los siete módulos disponibles completó la carga de 107
módulos (incluidas dependencias). Tras corregir los datos y el momento de
ejecución de las pruebas, la actualización conjunta de los siete módulos
terminó con **85 pruebas, 0 fallos y 0 errores** (resumen de Odoo).

Tras incorporar la dependencia del PR #269 y habilitar el módulo de nóminas:

* Prueba aislada de `payroll_account` y `payroll_account_employee_partner`:
  **28 pruebas, 0 fallos y 0 errores** (16 de OCA y 12 propias). En esta base
  temporal se creó antes un diario general; tres fixtures upstream lo
  presuponen y fallaron sin esa configuración. No se modificó código de OCA.
* Instalación de nóminas y actualización/regresión de los ocho módulos juntos:
  **97 pruebas, 0 fallos y 0 errores**, con 116 módulos cargados en el registro.
* Las 12 pruebas propias cubren asientos publicados y equilibrados con
  empleado/autoridad fiscal, impuesto y etiquetas de base; abonos; 465 corriente;
  delegación nativa para otras cuentas; contacto ausente; cuenta bancaria
  primaria; registros inválidos; cálculo de jornadas/reglas de alternancia;
  duplicados, períodos parciales, otro año y reglas ausentes; y contabilización
  multicompañía con cuentas company-dependent.

El módulo es instalable con la revisión exacta probada del PR; la rama oficial
OCA 19.0 por sí sola sigue sin proporcionar `payroll_account`. No hay bloqueo
por falta de implementación, pero su incorporación upstream sigue pendiente.

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
odoo-bin -d audit19 -i payroll_account_employee_partner,auto_journal_by_company,mrp_production_child_sale_info,product_blueprint_manager,product_configurator_attribute_price,ui_template_enhancements,web_binary_boe_download_fix,account_reconcile_n43_beneficiary --test-tags=/payroll_account_employee_partner,/auto_journal_by_company,/mrp_production_child_sale_info,/product_blueprint_manager,/product_configurator_attribute_price,/web_binary_boe_download_fix,/account_reconcile_n43_beneficiary --stop-after-init
```

Después repetir con `-u` en vez de `-i` para verificar actualización dentro de
19.0. Esto no equivale a migrar una BD 18.0 con OpenUpgrade. El workflow del
repositorio incluye ahora las pruebas nuevas de fabricación y descarga BOE.

### Revisiones de dependencias usadas

| Repositorio | SHA |
| --- | --- |
| odoo19 | `66af69fda24a7b0dc7b036bf1678b8850862c247` |
| payroll19 (rama oficial, revisión inicial) | `2eca6caafc74d4a592ee0ca75606b4c6e3ce75b9` |
| OCA/payroll PR #269 (nóminas y contabilidad) | `ef16a76b00462717d982b6a4f45082723255b1bf` |
| sale-workflow | `8a5e9df2842e28f1038137389e3c6dccea78bfe5` |
| product-attribute | `dc11b552a92ee5c394e49bc48b45d571e006393d` |
| l10n-spain | `750e3a3bb13a4f962293954579f87ad8da795aa1` |
| account-financial-reporting | `f48b4ea777c444256aa1c215ec3117d604b5feff` |
| server-ux | `af19073dc86443bad8590811649a54172a81a1ef` |
| account-reconcile | `e3d99f3dc4a61f44167ce0ce70e9a0a6ad0b7540` |
| bank-statement-import | `f22941f879c45ac2a258b2e7d88fe16a867e16d9` |

## Segunda revisión: conservación funcional

La revisión inicial y sus pruebas no bastaban para afirmar equivalencia total.
Se han reproducido y corregido dos diferencias:

1. **Diarios:** con el módulo sin onchange, cambiar la compañía en el formulario
   real de una factura en borrador conservaba el diario anterior. La prueba
   `test_native_company_change_on_draft_invoice` falla con esa retirada y pasa
   restaurando un onchange mínimo que utiliza `_search_default_journal` y el
   dominio nativo de compañía/sucursales. También se prueban compañía explícita
   diferente de la activa, abonos y diarios manuales válidos. La creación se
   mantiene en el núcleo: no necesita la sobrescritura anterior de `create`.
2. **Compras de componentes:** [Odoo 18](https://github.com/odoo/odoo/blob/18.0/addons/sale_purchase_stock/models/purchase_order.py)
   copiaba `sale_line_id` a las líneas de compra; [Odoo 19](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/sale_purchase_stock/models/purchase_order.py)
   limita esa copia al dropshipping. La adaptación inicial mantenía el vínculo
   al pedido mediante referencias, pero perdía el vínculo a su línea. Se restaura
   únicamente para compras originadas por componentes de OF con venta, mediante
   una marca de aprovisionamiento. La agrupación previa y la búsqueda de líneas
   existentes respetan esa línea de venta. Se mantiene la semántica nativa de
   las recepciones, que no deben computar como entrega del producto terminado.

La prueba real confirma cuatro ventas, las OF padre e hijas, compras separadas
por línea de origen y recepción. Dos ventas se confirman conjuntamente para
probar la agrupación de aprovisionamientos, y una venta MTO directa del mismo
componente comprueba que el flujo ordinario sigue separado. Las pruebas
anteriores solo creaban directamente una OF hija: ese hueco de cobertura
ha quedado cerrado.

**Planos:** el cambio conserva la búsqueda por movimientos destino e incorpora
como alternativa la línea de venta y las referencias de stock de Odoo 19.
No cambia la generación de planos, fórmulas, filtros ni permisos. Sigue la
limitación anterior: si hay varias ventas candidatas, imprime la primera;
no se ha convertido en un selector de ventas/planos.

Resultado de esta segunda revisión: **101 pruebas, 0 fallos y 0 errores**
en la actualización/regresión conjunta de los ocho módulos. Son cuatro
pruebas adicionales sobre las 97 anteriores: tres de diarios (compañía
explícita, abonos y cambio de compañía en formulario) y un flujo completo
de fabricación/compra. Las pruebas anteriores se conservan.

Criterio de conservación: una función documentada de 18.0 se mantiene en
19.0. Solo se retira su implementación propia cuando hay una implementación
nativa equivalente y comprobada para ese flujo. La existencia de un método
nativo de nombre similar no demuestra por sí sola esa equivalencia. Las
regresiones detectadas en esta segunda revisión corrigen la conclusión
demasiado amplia sobre diarios y compras de componentes.

## Revisión específica de eliminaciones — 9 de noviembre de 2026

Se revisaron los 20 archivos con líneas retiradas en el diff publicado
`11eac25f0b2bb43d5ab18efacd568108b474b577` →
`6d6435549e23e1f73fbf25d4bcd207c9a0b8bab9`.
La justificación detallada está en `DELETION_REVIEW_19.md`.

Se corrige otra diferencia del helper de diarios: el antiguo avisaba si no
había diario compatible y continuaba; el selector nativo lanza UserError.
La prueba reprodujo esa diferencia y ahora se conserva el aviso no bloqueante
al llamar al helper. La creación nativa sigue exigiendo un diario válido.
Se conservan mensajes de diagnóstico de evaluación, selección y diario
mantenido. Se restaura la llamada al onchange propio en su prueba original.

Se corrige expresamente la afirmación sobre `downloadFile(url)`: sí descarga
la URL con GET. El parche no estaba roto por ese motivo. La retirada se
justifica ahora mediante una prueba Chromium aislada que ejecuta el handler
real `BinaryField.onFileDownload` con tamaño binario y base64, y el helper GET
anterior. Los tres devuelven los mismos bytes y nombre del archivo BOE.
La prueba intercepta/observa XMLHttpRequest, sin falsear sus respuestas HTTP;
no automatiza la selección de archivo ni una descarga al disco del usuario.

Se comprueban además facturas generadas realmente desde pedidos de venta y
compra para justificar la eliminación de la sobrescritura `create`.

Validación final de esta revisión: **104 pruebas, 0 fallos, 0 errores y sin
pruebas omitidas** en actualización/regresión conjunta. Incluye el navegador
Chromium, facturas desde venta/compra y el aviso del helper sin diario.
El número cuenta métodos de prueba, no las cifras de fixtures/setup que Odoo
también muestra en el resumen por módulo. Ruff y `git diff --check`: correctos.
