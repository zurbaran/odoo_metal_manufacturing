from calendar import monthrange

from odoo import _, models
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_tax_details(self, line):
        """Normalize fiscal tags returned by OCA payroll_account.

        Supports both OCA recordsets and valid Odoo Many2many commands.
        """
        tax_ids, tags, repartition_id = super()._get_tax_details(line)

        if not tags:
            return tax_ids, tags, repartition_id

        if hasattr(tags, "ids"):
            tag_ids = tags.ids
        elif isinstance(tags, (list, tuple)) and tags and hasattr(tags[0], "id"):
            tag_ids = [tag.id for tag in tags]
        else:
            # Already in a supported ORM command format.
            return tax_ids, tags, repartition_id

        return tax_ids, [(6, 0, tag_ids)], repartition_id

    def action_payslip_done(self):
        """Protect alternance payslips from empty or invalid posting."""

        required_codes = {
            "FA26_BASE",
            "FA26_EXTRA",
            "FA26_DEV",
            "FA26_CC_T",
            "FA26_MEI_T",
            "FA26_DESEM_T",
            "FA26_FP_T",
            "FA26_BONIF_T",
            "FA26_IRPF",
            "FA26_NET",
            "FA26_CC_E",
            "FA26_MEI_E",
            "FA26_AT_EP_E",
            "FA26_DESEM_E",
            "FA26_FP_E",
            "FA26_FOGASA_E",
        }

        for record in self:
            if record.struct_id.code != "ES_FORM_ALT_2026":
                super(HrPayslip, record).action_payslip_done()
                continue

            slip = record.with_company(record.company_id)
            contract = slip.contract_id

            if slip.state not in ("draft", "verify"):
                raise UserError(_("La nómina no está pendiente de confirmación."))

            if slip.move_id:
                raise UserError(_("La nómina ya tiene un asiento contable."))

            if not contract or contract.company_id != slip.company_id:
                raise UserError(_("Contrato o compañía incorrectos."))

            if contract.employee_id != slip.employee_id:
                raise UserError(_("El empleado no coincide con el contrato."))

            if not slip.date_from or not slip.date_to:
                raise UserError(_("La nómina necesita un período válido."))

            if slip.date_from > slip.date_to:
                raise UserError(_("Las fechas de la nómina son incorrectas."))

            # La bonificación fija de 28 euros se ha
            # validado únicamente para meses completos.
            last_day = monthrange(
                slip.date_from.year,
                slip.date_from.month,
            )[1]

            if (
                slip.date_from.day != 1
                or slip.date_from.month != slip.date_to.month
                or slip.date_from.year != slip.date_to.year
                or slip.date_to.day != last_day
            ):
                raise UserError(
                    _(
                        "La bonificación del trabajador de 28 euros "
                        "solo está validada para mensualidades completas. "
                        "Revisar los períodos parciales antes de confirmar."
                    )
                )

            if slip.date_from.year != 2026 or slip.date_to.year != 2026:
                raise UserError(
                    _(
                        "Las reglas de formación en alternancia "
                        "están validadas para 2026. "
                        "Revisar cuotas y bonificaciones antes "
                        "de procesar nóminas de otro ejercicio."
                    )
                )

            if slip.date_from < contract.date_start or (
                contract.date_end and slip.date_to > contract.date_end
            ):
                raise UserError(
                    _("El período de nómina está fuera " "de las fechas del contrato.")
                )

            if slip.journal_id.company_id != slip.company_id:
                raise UserError(_("El diario de nóminas pertenece " "a otra compañía."))

            if not slip.credit_note:
                duplicates = self.search_count(
                    [
                        ("id", "!=", slip.id),
                        ("company_id", "=", slip.company_id.id),
                        ("employee_id", "=", slip.employee_id.id),
                        ("contract_id", "=", contract.id),
                        ("credit_note", "=", False),
                        ("state", "=", "done"),
                        ("date_from", "<=", slip.date_to),
                        ("date_to", ">=", slip.date_from),
                    ]
                )

                if duplicates:
                    raise UserError(
                        _(
                            "Ya existe una nómina confirmada "
                            "para este empleado y período."
                        )
                    )

            # Calcular jornadas cuando todavía no están registradas.
            if not slip.worked_days_line_ids:
                worked = slip.get_worked_day_lines(
                    contract, slip.date_from, slip.date_to
                )

                slip.write({"worked_days_line_ids": [(0, 0, row) for row in worked]})

            regular_days = slip.worked_days_line_ids.filtered(
                lambda line: line.code == "WORK100"
            )

            if len(regular_days) != 1 or regular_days.number_of_days <= 0:
                raise UserError(
                    _("No se han calculado jornadas " "retribuidas WORK100 válidas.")
                )

            # Evitar confirmar una nómina sin líneas salariales.
            if not slip.line_ids:
                slip.compute_sheet()

            current_codes = set(slip.line_ids.mapped("code"))
            missing = required_codes - current_codes

            if missing:
                raise UserError(
                    _("Faltan reglas salariales: ") + ", ".join(sorted(missing))
                )

            if len(current_codes) != len(slip.line_ids):
                raise UserError(_("La nómina contiene códigos salariales duplicados."))

            totals = {line.code: line.total for line in slip.line_ids}

            if totals["FA26_DEV"] <= 0 or totals["FA26_NET"] <= 0:
                raise UserError(
                    _(
                        "El bruto o neto de la nómina "
                        "no es válido para confirmación automática."
                    )
                )

            # OCA payroll_account genera y publica el asiento.
            # Se impide que OCA vuelva a calcular una nómina
            # que ya ha superado nuestras validaciones.
            super(
                HrPayslip,
                slip.with_context(without_compute_sheet=True),
            ).action_payslip_done()

        return True
