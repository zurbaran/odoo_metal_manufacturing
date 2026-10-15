# Reglas legibles y migración 18 → 19

## Alcance y responsabilidades

| Capa                   | Odoo 18 CE                                                                                               | Odoo 19 CE                                                                                             |
| ---------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Nativo `account`       | Modelos y tabla de mapeos `account.reconcile.model.partner.mapping`                                      | Un modelo de mapeo tiene una sola línea con tercero, sin cuenta; `mapped_partner_id` es calculado      |
| OCA                    | `account_reconcile_model_oca` aplica filtros y busca apuntes; `_retrieve_partner()` devuelve un registro | `account_reconcile_oca` selecciona reglas con SQL y `_retrieve_partner()` escribe el tercero por lotes |
| Addon N43              | Conserva conceptos y resuelve beneficiarios con los mapeos                                               | Conserva conceptos, resuelve en importación y en recuperación del tercero                              |
| Mejora de esta versión | Texto/opciones en condiciones y mapeos, detección de ambigüedad e instantáneas                           | Mismas opciones, adaptación a líneas nativas, recuperación de datos y filtros de 18                    |

Odoo ya ofrece **Contiene**, **No contiene** y **Regex**. Se conservan. No tiene
un editor completo de prefijo/sufijo/igualdad literal con opción de mayúsculas.
No se ha localizado una alternativa OCA actual que cubra ese hueco en ambas
arquitecturas. Se amplían los modelos existentes; no se añade otra tabla de
reglas ni otro motor de conciliación.

## Nueva configuración

En 18, el criterio del mapeo se configura en su línea. En 19, en
**Identificación del tercero**, seleccionando además una única línea nativa con
tercero y sin cuenta. Ejemplo: **Empieza por / COREMUTUA / No distinguir
mayúsculas**. En ambos casos puede indicarse una condición adicional sobre la
etiqueta bancaria completa, conservando diario, empresa, tercero e importe.

Los mapeos N43 reciben solamente el beneficiario extraído. Los CORE reciben la
etiqueta completa. No usar números de factura para identificar al proveedor.
**Contiene**, **Termina en** e **Igualdad exacta** son operaciones distintas; una
coincidencia exacta rechaza caracteres adicionales, incluso un salto de línea.

El texto, el tipo y la sensibilidad se guardan como configuración principal.
Se evalúan en Python en ambas ramas, escapando el texto literal internamente.
La opción avanzada conserva regex Python y su semántica `re.match`: para
buscar dentro de un texto hay que indicarlo, por ejemplo con `.*`.
Las condiciones nativas avanzadas de 19 siguen ejecutándose en PostgreSQL con
`~*`, y se validan en ambos motores. No se convierten automáticamente entre
sintaxis Python y PostgreSQL.

Los campos nativos de una regla legible contienen una condición neutra `.*`,
para seguir usando los contratos y cómputos nativos. La extensión aplica el
criterio real antes de aceptar la regla. En 19 añade un filtro de pares
modelo/movimiento a la consulta OCA: ni el texto ni una regex Python se envían
como patrón PostgreSQL. Los demás filtros continúan en Odoo/OCA.

## Qué ocurre con las reglas existentes

Actualizar el addon 18 **no reescribe ni simplifica automáticamente** las reglas.
La acción **Simplificar prefijos reconocidos** es optativa. Solo transforma
expresiones demostrablemente equivalentes a un prefijo literal, incluyendo
`(?i)^COREMUTUA.*` y la forma con parejas de caracteres de la solución temporal.
Conserva la expresión original y las diferencias de tratamiento de mayúsculas
que ya existían, incluidas las particularidades Unicode/ASCII.

DIGI, Iberdrola, IONOS, Canaluz, Birou, MAPFRE y Mutua pueden simplificarse si sus
expresiones tienen esa forma. Aguas Alicante (`\s+`) y Aguas Calpe (alternativas,
puntos y espacios variables) permanecen avanzadas. **No se sustituyen por una
regla Contiene ni por un texto con un espacio fijo**. Una expresión que no se
pueda demostrar equivalente se conserva.

Al desactivar un criterio legible se puede recuperar su condición nativa
archivada. No se borran modelos ni líneas de mapeo. La detección de dos terceros
distintos aplicables deja la resolución vacía, en lugar de elegir por secuencia.
Los terceros seleccionados explícitamente siguen teniendo prioridad.

## Migración de datos: orden de ejecución

1. En una **copia** de Camarbax18, actualizar primero este addon a `18.0.1.1.0`.
   Se guardan instantáneas de condiciones, estado, opciones de conciliación y
   mapeos. Revisar y simplificar solo los prefijos seguros si se desea.
2. Resolver el defecto independiente del script `account` de OpenUpgrade antes
   de ejecutar la migración. El addon 19 se carga después y no puede rescatar
   una excepción anterior de `account`. La solución temporal ya aplicada es
   válida para continuar; no es obligatorio deshacerla.
3. Migrar con OpenUpgrade y actualizar el addon 19 a `19.0.1.1.0`. Su migración
   utiliza la columna de enlace del mapeo legado creada por OpenUpgrade y
   recupera las definiciones originales por separado: etiqueta del modelo,
   etiqueta del mapeo y notas del mapeo se aplican con sus ámbitos y AND originales.
4. Se mantienen las restricciones de diario y empresa y los filtros de tercero.
   Los límites de importe absoluto de 18 se conservan, incluidos límites
   estrictos. El modelo 19 usa además límites nativos con signo compatibles.
   Una instantánea permite recuperar el estado activo previo de los modelos de
   identificación que OpenUpgrade archiva al convertir `invoice_matching`.
   **La extensión no escribe `trigger` ni cambia la decisión de automatización.**
5. Revisar la configuración migrada y probar importación/sugerencia en la copia.
   Los modelos antiguos y la tabla legada permanecen; los nuevos modelos llevan
   el ID de mapeo de origen. El proceso es idempotente.

Si ya se migró sin la actualización previa del addon 18, el adaptador recupera
las expresiones y relaciones que permanezcan en las tablas legadas. No inventa
el estado activo original si no existe instantánea. Para asegurar la conservación
completa, la vía recomendada es repetir la migración de prueba desde la copia 18
con las instantáneas creadas. No se debe reactivar masivamente todo lo archivado.

Al actualizar desde la primera versión 19 del addon, se conserva el comportamiento
que esa versión ya utilizaba: búsqueda Python con IGNORECASE para regex y casefold
para Contiene. No se amplía ni se ancla silenciosamente una expresión existente.
Las reglas nuevas y las recuperadas directamente de 18 usan su contrato explícito.

Las opciones de búsqueda de apuntes de OCA 18 (`unique_matching`, meses, orden,
moneda, etc.) se conservan en la instantánea. No se afirma que tengan un equivalente
operativo idéntico en Odoo/OCA 19: el addon resuelve terceros, no reconstruye el
motor de selección de pagos de 18. Revisar esas políticas al validar Odoo 19.

## Defecto independiente de OpenUpgrade

Fuente: `openupgrade_scripts/scripts/account/19.0.1.4/post-migration.py`, función
`account_reconcile_model_partner_mapping`. La versión revisada introduce flags
iniciales dentro de grupos/lookaheads y falla con `(?i)`.

Se prepara un parche independiente que sitúa un **IGNORECASE inicial común** al
principio de la expresión compuesta. No propone `(?i:...)` como arreglo universal:
PostgreSQL no admite esa construcción de Python. Si los flags difieren o hay flags
cuya equivalencia no está demostrada, se detiene con un mensaje explícito en vez
de eliminarlos o ampliar su alcance silenciosamente.

Ese parche es deliberadamente limitado al error de colocación de flags. El
script actual también mezcla con OR la etiqueta y las notas y compone alternativas
sin agrupar toda la condición. Esos problemas requieren otra revisión en OCA;
la adaptación del addon recupera los predicados originales para sus mapeos después
de `account`. No se presenta el parche de flags como solución general de traducción
entre motores ni como reparación completa de la migración de conciliación.

Búsquedas realizadas el 15-10-2026 en issues/PR de OCA/OpenUpgrade por `global flags`,
`regex`, `reconcile`, `mapping` y revisión de la PR #5509 y sus comentarios: no se
ha localizado una corrección específica del defecto de flags. El código actual
revisado todavía lo contiene.

## Validación y límites

Se ejecutan las pruebas del addon con Odoo 18/19 y PostgreSQL 16.2, las pruebas
anteriores de regresión, casos literales/avanzados y ambigüedad, restricciones,
recibos CORE y transferencias N43. Se prueba también actualización real del addon
desde sus revisiones 1.0 en bases desechables con reglas persistidas.

La recuperación 18→19 se prueba con la estructura legada y enlaces reales en
PostgreSQL, sin borrar configuraciones; no equivale a una migración completa de
Camarbax18 mediante OpenUpgrade. Esa prueba completa, un N43 original CajaMar y
la interfaz con un pago pendiente real siguen pendientes. Ninguna base de
producción se ha conectado ni modificado.

## Fuentes primarias revisadas

- [Odoo 18: modelos y mapeos](https://github.com/odoo/odoo/blob/18.0/addons/account/models/account_reconcile_model.py)
- [Odoo 19: líneas y mapped_partner_id](https://github.com/odoo/odoo/blob/19.0/addons/account/models/account_reconcile_model.py)
- [OCA 18: aplicación de condiciones](https://github.com/OCA/account-reconcile/blob/18.0/account_reconcile_model_oca/models/account_reconcile_model.py)
- [OCA 19: selección SQL de reglas](https://github.com/OCA/account-reconcile/blob/19.0/account_reconcile_oca/models/account_reconcile_model.py)
- [OCA 19: recuperación de terceros](https://github.com/OCA/account-reconcile/blob/19.0/account_reconcile_oca/models/account_bank_statement_line.py)
- [OpenUpgrade account post-migration](https://github.com/OCA/OpenUpgrade/blob/19.0/openupgrade_scripts/scripts/account/19.0.1.4/post-migration.py)
- [OpenUpgrade account pre-migration](https://github.com/OCA/OpenUpgrade/blob/19.0/openupgrade_scripts/scripts/account/19.0.1.4/pre-migration.py)
- [PR de migración account #5509](https://github.com/OCA/OpenUpgrade/pull/5509)
- [Documentación nativa de modelos](https://www.odoo.com/documentation/19.0/applications/finance/accounting/bank/reconciliation_models.html)
