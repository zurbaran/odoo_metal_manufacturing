# Justificación de las eliminaciones de la PR #39

Revisión: 9 de noviembre de 2026. [PR revisada](https://github.com/zurbaran/odoo_metal_manufacturing/pull/39).
Diff inicial revisado: base `11eac25f0b2bb43d5ab18efacd568108b474b577`,
cabecera `6d6435549e23e1f73fbf25d4bcd207c9a0b8bab9`. Este documento incluye las
correcciones realizadas como resultado de la revisión.

## Qué significan las líneas rojas

Había 20 archivos con alguna línea retirada. Solo se eliminaba por completo
un archivo de código: el parche JavaScript de BOE. Las demás eliminaciones
son sustituciones de métodos/bloques, documentación, versiones o formato.
No se eliminan tablas, campos propios, permisos, fórmulas de precios, planos,
reglas de conciliación, informes ni estructuras salariales mediante esta PR.
Esto describe el diff de esta PR frente a su base 19.0; no certifica todos los
cambios que ya existían entre las ramas 18.0 y 19.0 antes de esta PR.

## 1. Auto Journal by Company

Archivo: `auto_journal_by_company/models/account_move.py`.

### Sobrescritura de `create`: eliminada

Antes llamaba a `super().create(vals_list)`, separaba los movimientos con
`journal_id` explícito de los automáticos y llamaba al helper para los segundos.
Esa intervención sucedía después de que Odoo hubiera creado los movimientos.

Se retira porque la creación nativa selecciona el diario inicial y respeta
un diario explícito válido. Se comprueba la creación directa de facturas de
cliente/proveedor, compañía explícita distinta de la activa, diario manual,
abonos y, ahora, facturas generadas desde pedidos de venta y compra reales.
No se quita la asignación automática: cambia el responsable de esa fase.

Referencia: [selector nativo revisado](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/account/models/account_move.py#L898).

### Búsqueda manual de diario: sustituida

Se retiran el diccionario limitado a `out_invoice`/`in_invoice` y el `search`
con compañía exactamente igual. Se usan `_get_valid_journal_types`,
`_check_company_domain` y `_search_default_journal`: Odoo resuelve tipo,
moneda y compatibilidad con compañías/sucursales según su modelo 19.0.

Un diario manual válido se mantiene. Un diario de tipo incompatible no se
conserva solo por pertenecer a la misma compañía. Este segundo caso corrige
una inconsistencia, no elimina una selección manual válida. Los abonos y
recibos quedan dentro de los tipos nativos; las pruebas incluyen abonos.

### Onchange y helper: NO se eliminan

Permanecen `_auto_assign_journal` y `_onchange_company_or_type`.
La retirada completa ensayada inicialmente era incorrecta: la prueba con
`Form` reprodujo que cambiar la compañía podía conservar el diario anterior.
Se conserva esa corrección usando el selector nativo.

### Caso sin diario: restaurado en esta revisión

El helper antiguo dejaba un warning y continuaba si no encontraba diario.
El selector nativo lanza `UserError`. No eran equivalentes en ese caso.
Se añadió una prueba que falla con esa diferencia y se conserva el aviso
no bloqueante del helper. La creación/publicación nativas siguen exigiendo
un diario válido; no se permite contabilizar una factura sin diario.

### Comentarios y logging

Muchas líneas retiradas son docstrings y comentarios que repetían el código.
No tenían efecto en la selección de diario. Se conservan mensajes de evaluación,
diario mantenido, asignación y falta de diario. Los contadores/debug específicos
posteriores al `create` propio desaparecen con esa sobrescritura. No se promete
idéntico texto o cantidad de logs, ni equivalencia para herramientas externas
que analicen literalmente esos mensajes. No se borra un historial contable.

## 2. MRP Child MO Sale Propagation

### `stock.rule._prepare_mo_vals`: eliminada la duplicación

El método retirado llamaba a `super` y volvía a copiar `sale_line_id` a los
valores de la nueva OF. [El `sale_mrp` nativo revisado](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/sale_mrp/models/stock_rule.py#L7)
ya hace esa copia y es dependencia del módulo.

La conversión defensiva de recordset a ID del wrapper también desaparece:
el flujo propio introduce `sale_line_id` como ID numérico. No se afirma
compatibilidad con otro addon que incumpla ese contrato y entregue un
recordset en lugar del ID esperado por el flujo nativo.

La prueba completa confirma la venta y comprueba las OF padre e hija creadas
por el aprovisionamiento real, con la misma línea de venta. No depende solo
de crear manualmente una OF hija con el campo ya rellenado.

El archivo `stock_rule.py` NO se elimina: contiene ahora una intervención
necesaria para impedir que se agrupen compras de componentes de líneas de
venta distintas. Esa función es diferente del wrapper redundante retirado.

### `procurement_group_id.sale_id`: sustituido, no abandonado

La asignación al grupo antiguo se sustituye por un enlace a
`reference_ids.sale_ids`. [Odoo 19 usa esas referencias en `sale_mrp`](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/sale_mrp/models/mrp_production.py#L16).
El enlace añade la venta sin sustituir las ventas ya presentes. Se prueban OF
con venta y sin ella.

Esto conserva la relación entre documentos nuevos. La conversión de los
registros históricos de una BD 18 requiere la migración de stock/MRP del
núcleo; no se deduce de esta prueba ni se ha ejecutado sobre tu BD real.

### Propagación a componentes: se conserva y completa

No se elimina `stock.move._prepare_procurement_values`: sigue transmitiendo
la línea de venta del padre. Se añade una marca para distinguir las compras
de componentes de una venta MTO normal.

[Odoo 18 copiaba esa línea a compras](https://github.com/odoo/odoo/blob/18.0/addons/sale_purchase_stock/models/purchase_order.py),
pero [Odoo 19 limita la copia al dropshipping](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/sale_purchase_stock/models/purchase_order.py).
Se conserva la función original con código específico para compras de
componentes. Se comprueban cuatro ventas, dos confirmadas conjuntamente,
compras separadas por origen, compra MTO directa del mismo artículo y recepción
sin aumentar las cantidades entregadas del producto terminado.

En `models/__init__.py`, el import de `stock_rule` cambia de posición; sigue
presente. No se ha desactivado por quitar esa línea de su posición anterior.

## 3. Product Blueprint Manager

Se retira únicamente el fallback a `procurement_group_id.sale_id` en
`action_print_blueprint_mrp` y se sustituye por `sale_line_id.order_id` y
`reference_ids.sale_ids`.

Se conserva la primera búsqueda por movimientos destino, la comprobación de
permisos, el error si no hay venta y la llamada a `sale.order.action_print_blueprint`.
La prueba crea una OF sin movimientos destino, la vincula por referencias y
comprueba que devuelve la misma acción que imprimir desde el pedido.

La PR no retira código de generación SVG/PNG, fórmulas, condiciones, filtros,
permisos ni plantillas de informes. Persiste una limitación anterior: con varias
ventas candidatas se elige la primera. No se ha convertido esa selección en
una elección interactiva ni se certifica aquí la apariencia de los PDF.

## 4. Parche de descarga BOE

Se retira `web_binary_boe_download_fix/static/src/js/boe_binary_download_patch.esm.js`
y su entrada en `web.assets_backend`. El módulo sigue existiendo e instalable
para actualizar instalaciones que lo tenían; no se ejecuta una desinstalación.

El parche construía una URL GET para el asistente BOE y delegaba en el
comportamiento estándar para el resto. **La llamada `downloadFile(url)` sí
es válida. La explicación anterior de que descargaba el texto de la URL era
incorrecta y queda rectificada.**

Referencias: [helper GET](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/web/static/src/core/network/download.js#L295)
y [handler binario nativo](https://github.com/odoo/odoo/blob/66af69fda24a7b0dc7b036bf1678b8850862c247/addons/web/static/src/views/fields/binary/binary_field.js#L69).

La retirada se apoya en equivalencia comprobada para un asistente BOE guardado:

1. Ejecutar en Chromium el handler real `BinaryField.onFileDownload` con un
   valor representado por tamaño binario; comprobar su POST real.
2. Ejecutarlo con el valor base64; comprobar su POST real.
3. Ejecutar el helper GET que usaba el parche anterior.
4. Verificar en las tres respuestas estado 200, bytes exactos y nombre de archivo.

La prueba observa XMLHttpRequest, no falsea las respuestas HTTP. No es una
prueba de todos los navegadores, de cada declaración fiscal ni de la selección
de archivo en la interfaz: cubre el mecanismo compartido del campo binario.
La descarga HTTP aislada anterior no bastaba para justificar por sí sola la
retirada del parche. Para un asistente aún no guardado no se afirma equivalencia
adicional: el flujo BOE revisado guarda el asistente y abre su ID antes de descargar.

## 5. Resto de líneas retiradas: inventario completo por archivo

| Archivo o grupo | Qué desaparece del diff | Motivo y efecto |
| --- | --- | --- |
| `.github/workflows/odoo19-tests.yml` | Tres líneas antiguas de rutas, instalación y selección de pruebas | Se sustituyen por listas ampliadas. Se añaden nóminas, fabricación y descarga; N43 conserva su workflow separado. Se añade soporte de navegador. |
| `auto_journal_by_company/README.md` | Descripción repetida, comandos y referencia a Odoo 17 | Documentación actualizada a 19 y al código real; autoría permanece en el manifest. No es lógica ejecutable. |
| `auto_journal_by_company/__manifest__.py` | Versión y resumen antiguos | Incremento de versión y descripción; depende de `account` como antes. |
| `auto_journal_by_company/models/account_move.py` | `create`, búsqueda manual, comentarios y logs redundantes | Desglosado en el apartado 1; helper/onchange y aviso se conservan. |
| `auto_journal_by_company/tests/test_auto_journal.py` | Import y formato anteriores | Se añade `Form`/`tagged` y más casos. La llamada al onchange propio se restaura en esta revisión; no se sustituye su cobertura por una llamada nativa. |
| `mrp_production_child_sale_info/README.txt` | Diagrama y ejemplo con IDs/grupo antiguo | Se documenta el flujo actual con referencias, compras y límites MTO/MTS. |
| `mrp_production_child_sale_info/__manifest__.py` | Versión antigua | Incremento; se mantienen `sale_mrp` y `sale_purchase_stock`. |
| `mrp_production_child_sale_info/models/__init__.py` | Import en su posición original | El mismo import sigue más abajo; se añade compras. |
| `mrp_production_child_sale_info/models/mrp_production.py` | Acceso al grupo antiguo | Sustituido por referencias; apartado 2. |
| `mrp_production_child_sale_info/models/stock_rule.py` | Wrapper de `_prepare_mo_vals` | Nativo comprobado; se mantiene el archivo con la separación de compras. |
| `product_blueprint_manager/__manifest__.py` | Versión antigua | Incremento; no se retiran dependencias, datos ni informes. |
| `product_blueprint_manager/models/mrp_production.py` | Fallback antiguo y comentarios sobre él | Sustituido por las relaciones 19; apartado 3. |
| `product_configurator_attribute_price/tests/test_attribute_price_computation.py` | Import y saltos de línea de `.filtered` | Se añade `post_install`; lambda y aserciones se conservan. |
| `product_configurator_attribute_price/tests/test_description_generation.py` | Import y saltos de línea de `.filtered` | Mismo cambio de fase y formato; no se retira generación de descripciones. |
| `product_configurator_attribute_price/tests/test_price_formula.py` | Import anterior | Se añade `tagged`; no se quitan fórmulas ni casos. |
| `product_configurator_attribute_price/tests/test_security.py` | Import anterior | Se añade `tagged`; aserciones de permisos conservadas. |
| `web_binary_boe_download_fix/README.rst` | Justificación anterior del fallo de descarga | Sustituida y rectificada con evidencia del navegador; no es código. |
| `web_binary_boe_download_fix/__init__.py` | Comentario de archivo vacío | Se añaden las pruebas; no había lógica de descarga Python que se eliminase. |
| `web_binary_boe_download_fix/__manifest__.py` | Resumen/versión y registro del parche JS | Descarga nativa; módulo mantenido para actualización. |
| `web_binary_boe_download_fix/static/src/js/boe_binary_download_patch.esm.js` | Archivo completo, 45 líneas | Equivalencia del mecanismo comprobada en navegador; apartado 4. |

Las pruebas del configurador pasan a `post_install` porque al actualizar una BD
con módulos descendientes ya instalados, ejecutarlas con un registro parcial
producía errores en fixtures por campos obligatorios de esos otros módulos.
Se mantienen los casos y aserciones; cambia cuándo se ejecutan.

`payroll_account_employee_partner` es una incorporación en esta PR, no una
eliminación. En N43, plantillas UI y los modelos del configurador esta PR no
retira lógica de producción. Sus migraciones previas requieren distinguirse
del diff aquí examinado.

## Límites y evidencias

Las pruebas se ejecutan con Odoo CE 19 en la revisión
`66af69fda24a7b0dc7b036bf1678b8850862c247`, dependencias indicadas en
`MIGRATION_AUDIT_19.md` y datos temporales. No se modifica tu base de producción.
No se ha demostrado una migración de los datos históricos de una copia real
18→19 con OpenUpgrade, ni compatibilidad con cualquier addon externo o
navegador. El resultado no significa que toda línea roja sea prescindible por
ser roja: cada eliminación funcional se liga al reemplazo y prueba indicados.

Validación final de esta revisión: **104 pruebas, 0 fallos, 0 errores y sin
pruebas omitidas** en actualización/regresión conjunta. Incluye el navegador
Chromium, facturas desde venta/compra y el aviso del helper sin diario.
El número cuenta métodos de prueba, no las cifras de fixtures/setup que Odoo
también muestra en el resumen por módulo. Ruff y `git diff --check`: correctos.
