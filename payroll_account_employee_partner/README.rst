Payroll Accounting Employee Partner
===================================

Extensión de OCA Payroll Accounting para Odoo 18 Community.

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
