Payroll Accounting Employee Partner
===================================

Extensión de OCA Payroll Accounting para Odoo 19 Community.

Estado de la migración
----------------------

Instalable con la dependencia de OCA/payroll PR #269:
https://github.com/OCA/payroll/pull/269

Revisión utilizada: ``ef16a76b00462717d982b6a4f45082723255b1bf``.
El PR sigue abierto y tiene revisiones aprobadas; aún no está integrado en
la rama oficial 19.0. Desplegar el repositorio de esa revisión, con ``payroll``
y ``payroll_account`` en el addons-path. La dependencia no se copia en este
repositorio. El workflow de pruebas utiliza el mismo SHA fijo.

Se han adaptado las fechas de contrato a ``hr.version.contract_date_start``
y ``contract_date_end``, y la cuenta bancaria a ``primary_bank_account_id``.
Las cuentas y los impuestos se resuelven en la compañía de la nómina.
Se normalizan los recordsets/listas de etiquetas fiscales que devuelve
``_get_tax_details`` del PR, sin sustituir el motor contable de OCA.

No se certifica la corrección legal de las reglas salariales ES_FORM_ALT_2026.

Descripción
-----------

Este módulo mejora la contabilización automática de nóminas:

* Asigna el contacto del empleado a las cuentas de remuneraciones
  pendientes de pago (465).
* Identifica al empleado en las bases salariales sujetas a retención (640).
* Normaliza las etiquetas fiscales Many2many generadas por
  OCA payroll_account.
* Protege la confirmación de nóminas de formación en alternancia,
  calculando jornadas y reglas salariales cuando sea necesario.
* Valida las fechas, la empresa, el contrato y las reglas aplicables
  a la estructura ES_FORM_ALT_2026.
* Impide duplicar nóminas confirmadas para un mismo período.

El PR de OCA ya asigna el empleado a cuentas ``liability_current`` y
``asset_receivable``. Esta extensión mantiene las reglas españolas adicionales:
empleado obligatorio en 465 (también ``liability_payable``) y bases 640 con
retención, y contacto del registro de contribución en 475100/476000.

Configuración
-------------

Requiere el módulo OCA ``payroll_account``.

Las cuentas contables, las reglas salariales, el diario de nóminas
y los impuestos se configuran en Odoo.

La estructura ``ES_FORM_ALT_2026`` debe contener sus 16 reglas
salariales y estar vinculada al contrato correspondiente.

Funcionamiento
--------------

Al confirmar una nómina de formación en alternancia, el módulo
comprueba sus datos, calcula las jornadas y reglas pendientes
y permite que OCA Payroll Accounting genere el asiento contable.

El asiento queda vinculado a la nómina. Las bases y retenciones
fiscales mantienen su identificación para los modelos AEAT.

Limitaciones
------------

Las reglas ES_FORM_ALT_2026 están limitadas al ejercicio 2026.

Las cuotas y bonificaciones deben revisarse ante cambios normativos
o contractuales. El módulo no calcula por sí mismo las
bonificaciones empresariales de formación y tutorización.

Licencia
--------

AGPL-3.0-or-later
