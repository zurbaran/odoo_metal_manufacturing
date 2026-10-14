# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestN43Beneficiary19(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.holder = cls.env["res.partner"].create(
            {"name": "ANTONIO JOSE CABALLERO ALCARAZ"}
        )
        cls.templa = cls.env["res.partner"].create({"name": "Templaglass SL"})
        cls.salinas = cls.env["res.partner"].create({"name": "Vidrios Salinas"})
        cls.bank = cls.env["account.journal"].create(
            {
                "name": "N43 Test",
                "code": "N43",
                "type": "bank",
                "company_id": cls.company.id,
                "n43_partner_search": "none",
                "n43_beneficiary_enabled": True,
                "n43_ignored_partner_ids": [Command.link(cls.holder.id)],
            }
        )
        cls.env["account.reconcile.model"].search(
            [("company_id", "=", cls.company.id)]
        ).active = False
        cls.templa_model = cls._mapping(cls.templa, r"(?i).*TEMPLAGLASS.*")
        cls.salinas_model = cls._mapping(cls.salinas, r"(?i).*VIDRIOS SALINAS.*")

    @classmethod
    def _mapping(cls, partner, regex):
        model = cls.env["account.reconcile.model"].create(
            {
                "name": "N43 mapping: " + partner.name,
                "company_id": cls.company.id,
                "trigger": "manual",
                "match_journal_ids": [Command.link(cls.bank.id)],
                "match_label": "match_regex",
                "match_label_param": regex,
                "line_ids": [Command.create({"partner_id": partner.id})],
            }
        )
        assert model.mapped_partner_id == partner
        return model

    def _line(self, beneficiary="TEMPLAGLASS SL", **extra):
        vals = {
            "journal_id": self.bank.id,
            "company_id": self.company.id,
            "date": fields.Date.today(),
            "partner_name": self.holder.name,
            "payment_ref": "ANTONIO JOSE CABALLERO CASHFra.261870 " + beneficiary,
            "amount": -39.77,
            "n43_imported": True,
            "n43_complementary_concepts": {
                "01": [self.holder.name, ""],
                "03": ["CASHFra.261870", ""],
                "05": [beneficiary, ""],
            },
        }
        vals.update(extra)
        return self.env["account.bank.statement.line"].with_context(
            skip_retrieve_partner=True
        ).create(vals).with_context(skip_retrieve_partner=False)

    def test_partner_mapping(self):
        line = self._line()
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.templa)
        self.assertFalse(line.is_reconciled)

    def test_other_partner(self):
        line = self._line("VIDRIOS SALINAS S.L.")
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.salinas)

    def test_preserve_valid_partner(self):
        line = self._line(partner_id=self.salinas.id)
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.salinas)

    def test_replace_holder(self):
        line = self._line(partner_id=self.holder.id)
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.templa)

    def test_conflicting_mapping_clears_holder(self):
        self._mapping(self.salinas, r"(?i).*TEMPLAGLASS.*")
        line = self._line(partner_id=self.holder.id)
        line._retrieve_partner()
        self.assertFalse(line.partner_id)

    def test_numeric_reference_does_not_map(self):
        self.templa_model.active = False
        line = self._line("UNKNOWN SUPPLIER", partner_id=self.holder.id)
        line._retrieve_partner()
        self.assertFalse(line.partner_id)

    def test_core_direct_debit_is_unchanged(self):
        line = self._line(payment_ref="CORETGSS", partner_id=self.holder.id)
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.holder)

    def test_disabled_journal(self):
        self.bank.n43_beneficiary_enabled = False
        line = self._line(partner_id=self.holder.id)
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.holder)

    def test_missing_structured_record_does_not_use_legacy(self):
        self.bank.n43_allow_legacy_lines = True
        line = self._line(partner_id=self.holder.id, n43_complementary_concepts={})
        line._retrieve_partner()
        self.assertFalse(line.partner_id)

    def test_amount_filter(self):
        self.templa_model.match_amount = "greater"
        self.templa_model.match_amount_min = 100
        line = self._line(partner_id=self.holder.id)
        line._retrieve_partner()
        self.assertFalse(line.partner_id)

    def test_skip_context(self):
        line = self._line(partner_id=self.holder.id)
        line.with_context(skip_retrieve_partner=True)._retrieve_partner()
        self.assertEqual(line.partner_id, self.holder)

    def test_legacy_opt_in(self):
        line = self._line(
            partner_id=self.holder.id, n43_imported=False,
            n43_complementary_concepts=False,
        )
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.holder)
        self.bank.n43_allow_legacy_lines = True
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.templa)

    def test_invalid_legacy_regex(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.bank.n43_legacy_beneficiary_regex = "["

    def test_import_populates_partner_before_create(self):
        wizard = self.env["account.statement.import"].create({})
        raw = {
            "conceptos": {
                "01": (self.holder.name, ""),
                "03": ("CASHFra.261870", ""),
                "05": ("TEMPLAGLASS SL", ""),
            },
            "importe": -39.77,
            "referencia1": "",
            "referencia2": "",
            "fecha_valor": fields.Date.today(),
            "fecha_oper": fields.Date.today(),
        }
        group = {
            "lines": [raw],
            "saldo_ini": 100,
            "saldo_fin": 60.23,
            "divisa": "978",
            "cuenta": "1234567890",
        }
        parsed = wizard._parse_single_file_n43([group])
        completed = wizard._complete_stmts_vals(parsed[2], self.bank, parsed[1])
        vals = completed[0]["transactions"][0]
        self.assertEqual(vals["n43_complementary_concepts"]["05"][0], "TEMPLAGLASS SL")
        self.assertEqual(vals["partner_id"], self.templa.id)
        self.assertNotIn("n43_line", vals)
