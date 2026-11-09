from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPayrollPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Payroll migration employee"}
        )
        cls.employee.version_id.write(
            {
                "date_version": "2026-01-01",
                "contract_date_start": "2026-01-01",
                "wage": 1000,
                "resource_calendar_id": cls.env.company.resource_calendar_id.id,
            }
        )
        cls.expense = cls._account("640001", "expense")
        cls.payable = cls._account("465001", "liability_payable")
        cls.current = cls._account("465002", "liability_current")
        cls.withholding = cls._account("475100", "liability_current")
        cls.social = cls._account("476000", "liability_current")
        cls.authority = cls.env["res.partner"].create({"name": "Tax authority fixture"})
        cls.register = cls.env["hr.contribution.register"].create(
            {
                "name": "Tax register",
                "partner_id": cls.authority.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Payroll migration",
                "code": "PMIG",
                "type": "general",
            }
        )
        cls.base = cls._rule("MIG_BASE", account_debit=cls.expense.id, amount_fix=1000)
        cls.tax_rule = cls._rule(
            "MIG_TAX",
            account_credit=cls.withholding.id,
            register_id=cls.register.id,
            amount_fix=150,
        )
        cls.net = cls._rule("MIG_NET", account_credit=cls.payable.id, amount_fix=850)
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Payroll fixture withholding",
                "amount": 15,
                "type_tax_use": "purchase",
            }
        )
        cls.tag = cls.env["account.account.tag"].create(
            {
                "name": "Payroll fiscal fixture",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        invoice_reps = cls.tax.invoice_repartition_line_ids
        invoice_reps.filtered(
            lambda rep: rep.repartition_type == "base"
        ).tag_ids = cls.tag
        invoice_reps.filtered(
            lambda rep: rep.repartition_type == "tax"
        ).account_id = cls.withholding
        cls.tax_rule.write({"account_tax_id": cls.tax.id, "tax_base_id": cls.base.id})
        cls.structure = cls.env["hr.payroll.structure"].create(
            {
                "name": "Migration fixture",
                "code": "MIGRATION",
                "parent_id": False,
                "rule_ids": [Command.set((cls.base | cls.tax_rule | cls.net).ids)],
            }
        )

    @classmethod
    def _account(cls, code, kind):
        return cls.env["account.account"].create(
            {
                "name": "Payroll " + code,
                "code": code,
                "account_type": kind,
                "reconcile": kind == "liability_payable",
            }
        )

    @classmethod
    def _rule(cls, code, **values):
        return cls.env["hr.salary.rule"].create(
            {
                "name": code,
                "code": code,
                "amount_select": "fix",
                **values,
            }
        )

    def _slip(self, structure=None, **values):
        structure = structure or self.structure
        self.employee.version_id.struct_id = structure
        return self.env["hr.payslip"].create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.employee.version_id.id,
                "struct_id": structure.id,
                "journal_id": self.journal.id,
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                **values,
            }
        )

    def _line(self, slip, rule):
        return self.env["hr.payslip.line"].create(
            {
                "slip_id": slip.id,
                "salary_rule_id": rule.id,
                "name": rule.name,
                "code": rule.code,
                "amount": 100,
            }
        )

    def test_posting_preserves_employee_authority_and_fiscal_tags(self):
        slip = self._slip()
        slip.action_payslip_done()
        self.assertEqual(slip.move_id.state, "posted")
        lines = slip.move_id.line_ids
        for account in (self.expense, self.payable):
            self.assertEqual(
                lines.filtered(
                    lambda row, account=account: row.account_id == account
                ).partner_id,
                self.employee.work_contact_id,
            )
        tax_line = lines.filtered(lambda row: row.account_id == self.withholding)
        self.assertEqual(tax_line.partner_id, self.authority)
        self.assertTrue(tax_line.tax_repartition_line_id)
        base_line = lines.filtered(lambda row: row.account_id == self.expense)
        self.assertIn(self.tag, base_line.tax_tag_ids)
        self.assertIn(self.tax, base_line.tax_ids)
        self.assertAlmostEqual(sum(lines.mapped("balance")), 0)

    def test_credit_note_reverses_amounts_and_keeps_partners(self):
        slip = self._slip(credit_note=True)
        slip.action_payslip_done()
        lines = slip.move_id.line_ids
        self.assertEqual(
            lines.filtered(lambda row: row.account_id == self.expense).credit, 1000
        )
        net = lines.filtered(lambda row: row.account_id == self.payable)
        self.assertEqual(net.debit, 850)
        self.assertEqual(net.partner_id, self.employee.work_contact_id)
        self.assertAlmostEqual(sum(lines.mapped("balance")), 0)

    def test_465_current_also_uses_employee_not_register(self):
        self.net.write(
            {"account_credit": self.current.id, "register_id": self.register.id}
        )
        line = self._line(self._slip(), self.net)
        self.assertEqual(line._get_partner_id(True), self.employee.work_contact_id.id)

    def test_other_accounts_delegate_to_oca(self):
        other = self._account("410001", "liability_payable")
        self.net.write({"account_credit": other.id, "register_id": self.register.id})
        self.assertEqual(
            self._line(self._slip(), self.net)._get_partner_id(True), self.authority.id
        )
        self.base.tax_line_ids = False
        self.assertFalse(self._line(self._slip(), self.base)._get_partner_id(False))

    def test_missing_employee_contact_is_rejected(self):
        self.employee.work_contact_id = False
        self.assertFalse(self.employee.primary_bank_account_id)
        with self.assertRaises(UserError):
            self._line(self._slip(), self.net)._get_partner_id(True)

    def test_bank_contact_fallback_uses_odoo19_primary_account(self):
        partner = self.employee.work_contact_id
        bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "PAYROLL-MIGRATION-001",
                "partner_id": partner.id,
            }
        )
        self.employee.bank_account_ids = bank
        self.employee.work_contact_id = False
        self.assertEqual(self.employee.primary_bank_account_id, bank)
        self.assertEqual(
            self._line(self._slip(), self.net)._get_partner_id(True), partner.id
        )

    def test_authority_accounts_require_valid_register(self):
        for account in (self.withholding, self.social):
            self.tax_rule.write({"account_credit": account.id, "register_id": False})
            with self.assertRaises(UserError):
                self._line(self._slip(), self.tax_rule)._get_partner_id(True)
        self.tax_rule.register_id = self.register
        self.register.company_id = self.env["res.company"].create(
            {"name": "Wrong register company"}
        )
        with self.assertRaises(UserError):
            self._line(self._slip(), self.tax_rule)._get_partner_id(True)

    def _alternance(self):
        codes = [
            "BASE",
            "EXTRA",
            "DEV",
            "CC_T",
            "MEI_T",
            "DESEM_T",
            "FP_T",
            "BONIF_T",
            "IRPF",
            "NET",
            "CC_E",
            "MEI_E",
            "AT_EP_E",
            "DESEM_E",
            "FP_E",
            "FOGASA_E",
        ]
        rules = self.env["hr.salary.rule"]
        for code in codes:
            values = {"amount_fix": 1}
            if code == "DEV":
                values.update(account_debit=self.expense.id, amount_fix=1000)
            elif code == "NET":
                values.update(account_credit=self.payable.id, amount_fix=1000)
            rules |= self._rule("FA26_" + code, **values)
        return self.env["hr.payroll.structure"].create(
            {
                "name": "Synthetic alternance fixture",
                "code": "ES_FORM_ALT_2026",
                "parent_id": False,
                "rule_ids": [Command.set(rules.ids)],
            }
        )

    def test_alternance_computes_days_and_rules_then_posts(self):
        slip = self._slip(self._alternance())
        self.assertFalse(slip.line_ids)
        slip.action_payslip_done()
        self.assertEqual(slip.state, "done")
        self.assertEqual(slip.move_id.state, "posted")
        self.assertEqual(len(slip.line_ids), 16)
        self.assertGreater(
            slip.worked_days_line_ids.filtered(
                lambda row: row.code == "WORK100"
            ).number_of_days,
            0,
        )
        with self.assertRaises(UserError):
            slip.action_payslip_done()

    def test_alternance_rejects_duplicate_period(self):
        structure = self._alternance()
        self._slip(structure).action_payslip_done()
        with self.assertRaises(UserError):
            self._slip(structure).action_payslip_done()

    def test_alternance_rejects_partial_month_and_other_year(self):
        structure = self._alternance()
        for dates in [
            {"date_from": "2026-01-02"},
            {"date_from": "2027-01-01", "date_to": "2027-01-31"},
        ]:
            with self.assertRaises(UserError):
                self._slip(structure, **dates).action_payslip_done()

    def test_alternance_rejects_missing_rules(self):
        structure = self._alternance()
        structure.rule_ids = structure.rule_ids.filtered(
            lambda row: row.code != "FA26_FP_T"
        )
        with self.assertRaisesRegex(UserError, "FA26_FP_T"):
            self._slip(structure).action_payslip_done()

    def test_posting_uses_payslip_company_for_property_accounts(self):
        company = self.env["res.company"].create({"name": "Payroll second company"})
        employee = (
            self.env["hr.employee"]
            .with_company(company)
            .create(
                {
                    "name": "Second company employee",
                    "company_id": company.id,
                }
            )
        )
        employee.version_id.write(
            {
                "date_version": "2026-01-01",
                "contract_date_start": "2026-01-01",
            }
        )
        Account = self.env["account.account"].with_company(company)
        debit = Account.create(
            {
                "name": "Second company wages",
                "code": "640123",
                "account_type": "expense",
            }
        )
        credit = Account.create(
            {
                "name": "Second company salaries",
                "code": "465123",
                "account_type": "liability_current",
            }
        )
        rule = self._rule(
            "MULTI",
            company_id=False,
            amount_fix=100,
            account_debit=self.expense.id,
            account_credit=self.payable.id,
        )
        rule.with_company(company).write(
            {"account_debit": debit.id, "account_credit": credit.id}
        )
        structure = (
            self.env["hr.payroll.structure"]
            .with_company(company)
            .create(
                {
                    "name": "Second company structure",
                    "code": "MULTI",
                    "parent_id": False,
                    "rule_ids": [Command.set(rule.ids)],
                }
            )
        )
        employee.version_id.struct_id = structure
        journal = (
            self.env["account.journal"]
            .with_company(company)
            .create(
                {
                    "name": "Second payroll",
                    "code": "SEC",
                    "type": "general",
                }
            )
        )
        slip = (
            self.env["hr.payslip"]
            .with_company(company)
            .create(
                {
                    "company_id": company.id,
                    "employee_id": employee.id,
                    "contract_id": employee.version_id.id,
                    "struct_id": structure.id,
                    "journal_id": journal.id,
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                }
            )
            .with_company(self.env.company)
        )
        slip.action_payslip_done()
        self.assertEqual(slip.move_id.company_id, company)
        self.assertEqual(slip.move_id.line_ids.account_id, debit | credit)
        self.assertEqual(slip.move_id.state, "posted")
