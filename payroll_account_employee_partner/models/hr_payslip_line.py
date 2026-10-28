from odoo import models
from odoo.exceptions import UserError


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def _get_partner_id(self, credit_account):
        """Use the current payslip employee for salary-related entries.

        Scope:
          - Credit entries to employee remuneration accounts 465*
          - Debit entries to taxable salary accounts 640*

        Other accounts retain the standard OCA behavior.
        """
        self.ensure_one()

        company = self.slip_id.company_id
        rule = self.salary_rule_id.with_company(company)

        account = rule.account_credit if credit_account else rule.account_debit

        code = account.code or ""

        is_employee_payable = (
            credit_account
            and code.startswith("465")
            and account.account_type
            in (
                "liability_payable",
                "liability_current",
            )
        )

        is_taxable_salary = (
            not credit_account and code.startswith("640") and bool(rule.tax_line_ids)
        )

        if is_employee_payable or is_taxable_salary:
            employee = self.slip_id.employee_id

            partner = employee.work_contact_id or employee.bank_account_id.partner_id

            if not partner:
                raise UserError(
                    f"El empleado {employee.name} no tiene contacto asociado "
                    "para contabilizar la nómina."
                )

            return partner.id

        return super()._get_partner_id(credit_account)
