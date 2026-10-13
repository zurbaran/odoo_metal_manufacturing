# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestN43Beneficiary(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.holder = cls.env["res.partner"].create(
            {"name": "ANTONIO JOSE CABALLERO ALCARAZ"}
        )
        cls.bank = cls.env["account.journal"].create(
            {
                "name": "N43 test bank",
                "code": "N43",
                "type": "bank",
                "company_id": cls.company.id,
                "n43_partner_search": "none",
                "n43_beneficiary_enabled": True,
                "n43_ignored_partner_ids": [Command.link(cls.holder.id)],
            }
        )
        cls.templa = cls.env["res.partner"].create({"name": "Templaglass S.L."})
        cls.salinas = cls.env["res.partner"].create({"name": "Vidrios Salinas, S.L."})
        cls.vbh = cls.env["res.partner"].create({"name": "VBH Iberia, S.L."})
        cls.forta = cls.env["res.partner"].create(
            {"name": "FORTA FABRICACIONES ORTOPEDICAS ALBACETE"}
        )
        cls.miexal = cls.env["res.partner"].create({"name": "Miexal Extrusión"})
        cls.client = cls.env["res.partner"].create({"name": "ELENA TORRES LUKIANCHUK"})
        cls.digi = cls.env["res.partner"].create({"name": "DIGI test"})
        # Keep only our controlled mapping models active in this fixture.
        cls.env["account.reconcile.model"].search(
            [("company_id", "=", cls.company.id)]
        ).active = False
        cls.templa_model = cls._mapping(cls.templa, r"(?i).*\bTEMPLAGLASS\b.*")
        cls.salinas_model = cls._mapping(cls.salinas, r"(?i).*\bVIDRIOS SALINAS\b.*")
        cls.vbh_model = cls._mapping(cls.vbh, r"(?i).*\bVBH\b.*")
        cls.forta_model = cls._mapping(cls.forta, r"(?i).*\bFORTA\b.*")
        cls._mapping(cls.digi, r"(?i).*COREDIGI.*", match_nature="both")
        cls.transit = cls.env["account.account"].create(
            {
                "name": "Test outstanding supplier payments",
                "code": "572012",
                "account_type": "asset_current",
                "reconcile": True,
                "company_ids": [Command.link(cls.company.id)],
            }
        )

    @classmethod
    def _mapping(cls, partner, regex, **extra):
        return cls.env["account.reconcile.model"].create(
            {
                "name": f"Payment {partner.name} - suggestion",
                "company_id": cls.company.id,
                "rule_type": "invoice_matching",
                "auto_reconcile": False,
                "match_nature": "amount_paid",
                "match_partner": True,
                "match_partner_ids": [Command.link(partner.id)],
                "match_journal_ids": [Command.link(cls.bank.id)],
                "partner_mapping_line_ids": [
                    Command.create(
                        {"partner_id": partner.id, "payment_ref_regex": regex}
                    )
                ],
                **extra,
            }
        )

    def _line(self, document="CASHFra.261870", beneficiary="TEMPLAGLASS SL", **extra):
        return (
            self.env["account.bank.statement.line"]
            .with_context(skip_retrieve_partner=True)
            .create(
                {
                    "journal_id": self.bank.id,
                    "date": fields.Date.today(),
                    "partner_name": self.holder.name,
                    "payment_ref": (
                        f"{self.holder.name} 48353047D {document} {beneficiary}"
                    ),
                    "amount": -39.77,
                    "n43_imported": isinstance(
                        extra.get("n43_complementary_concepts", {}), dict
                    ),
                    "n43_complementary_concepts": {
                        "01": [self.holder.name, ""],
                        "02": ["48353047D", ""],
                        "03": [document, ""],
                        "05": [beneficiary, ""],
                    },
                    **extra,
                }
            )
            .with_context(skip_retrieve_partner=False)
        )

    def _outstanding(self, partner, reference="261870"):
        move = self.env["account.move"].create(
            {
                "journal_id": self.company_data["default_journal_misc"].id,
                "date": fields.Date.today(),
                "ref": reference,
                "line_ids": [
                    Command.create(
                        {
                            "name": reference,
                            "partner_id": partner.id,
                            "account_id": self.transit.id,
                            "credit": 39.77,
                        }
                    ),
                    Command.create(
                        {
                            "name": reference,
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                            "debit": 39.77,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move.line_ids.filtered(lambda line: line.account_id == self.transit)

    def test_templaglass_references(self):
        for reference in ("261405", "261649", "261689", "261870", "261934"):
            with self.subTest(reference=reference):
                line = self._line(document=f"CASHFra.{reference}")
                original = line.read(
                    ["partner_name", "payment_ref", "ref", "narration"]
                )
                self.assertEqual(line._retrieve_partner(), self.templa)
                self.assertEqual(
                    line.read(["partner_name", "payment_ref", "ref", "narration"]),
                    original,
                )
                self.assertFalse(line.partner_id)

    def test_vidrios_salinas_references(self):
        for reference in ("2603412", "2603413", "2603943", "2604138", "2604572"):
            with self.subTest(reference=reference):
                line = self._line(f"CASHFra.{reference}", "VIDRIOS SALINAS S.L.")
                self.assertEqual(line._retrieve_partner(), self.salinas)

    def test_vbh_alias(self):
        line = self._line("CASHOferta n.SQ054744", "VBH Malum, S.L.")
        self.assertEqual(line._retrieve_partner(), self.vbh)

    def test_incoming_client_is_preserved(self):
        line = self._line(
            "SO295",
            self.holder.name,
            amount=100,
            partner_name=self.client.name,
        )
        self.assertEqual(line._retrieve_partner(), self.client)

    def test_direct_debits_are_unchanged(self):
        for label in (
            "COREDIGI",
            "COREIONOS",
            "CORECANALUZ",
            "COREAGUAS",
            "COREMAPFRE",
            "CORETGSS",
            "CORECDAD PPTARIOS",
            "CORECP. HERCULES",
        ):
            with self.subTest(label=label):
                line = self._line(payment_ref=label, partner_name=False)
                self.assertFalse(line._n43_is_outgoing_transfer())
                if label == "COREDIGI":
                    self.assertEqual(line._retrieve_partner(), self.digi)

    def test_unknown_or_missing_beneficiary(self):
        for beneficiary in ("", "UNKNOWN SUPPLIER", self.holder.name):
            with self.subTest(beneficiary=beneficiary):
                self.assertFalse(
                    self._line(beneficiary=beneficiary)._retrieve_partner()
                )

    def test_forta_does_not_match_miexal_reference(self):
        wrong_aml = self._outstanding(self.miexal, "26/6580")
        correct_aml = self._outstanding(self.forta, "26/6580")
        line = self._line("CASHFra. 26/6580", self.forta.name)
        partner = line._retrieve_partner()
        self.assertEqual(partner, self.forta)
        domain = self.forta_model._get_invoice_matching_amls_domain(line, partner)
        candidates = self.env["account.move.line"].search(domain)
        self.assertIn(correct_aml, candidates)
        self.assertNotIn(wrong_aml, candidates)
        result = self.forta_model._apply_rules(line, partner)
        self.assertEqual(result["amls"], correct_aml)
        self.assertFalse(result.get("auto_reconcile"))
        self.assertFalse(line.is_reconciled)

    def test_no_open_move_creates_nothing(self):
        line = self._line()
        models = ("account.move", "account.payment", "account.partial.reconcile")
        before = {name: self.env[name].search_count([]) for name in models}
        partner = line._retrieve_partner()
        self.assertEqual(partner, self.templa)
        self.assertFalse(self.templa_model._apply_rules(line, partner))
        self.assertEqual(
            before, {name: self.env[name].search_count([]) for name in models}
        )
        self.assertFalse(line.is_reconciled)

    def test_oca_suggests_outstanding_payment(self):
        expected = self._outstanding(self.templa)
        line = self._line()
        result = self.templa_model._apply_rules(line, line._retrieve_partner())
        self.assertEqual(result["amls"], expected)
        self.assertFalse(result.get("auto_reconcile"))
        self.assertFalse(line.is_reconciled)

    def test_disabled_journal_preserves_upstream(self):
        self.bank.n43_beneficiary_enabled = False
        self.assertEqual(self._line()._retrieve_partner(), self.holder)

    def test_non_n43_requires_explicit_legacy_opt_in(self):
        line = self._line(n43_complementary_concepts=False)
        self.assertEqual(line._retrieve_partner(), self.holder)
        self.bank.n43_allow_legacy_lines = True
        self.assertEqual(line._retrieve_partner(), self.templa)
        line = self._line(
            "CASHOferta n.SQ054744", "VBH Malum, S.L.", n43_complementary_concepts=False
        )
        self.assertEqual(line._retrieve_partner(), self.vbh)

    def test_numeric_reference_cannot_identify_partner(self):
        self._mapping(self.miexal, r".*261870.*")
        self.templa_model.active = False
        self.assertFalse(self._line()._retrieve_partner())
        self.bank.n43_allow_legacy_lines = True
        self.assertFalse(
            self._line(n43_complementary_concepts=False)._retrieve_partner()
        )

    def test_imported_holder_and_explicit_beneficiary(self):
        self.assertEqual(
            self._line(partner_id=self.holder.id)._retrieve_partner(), self.templa
        )
        self.assertEqual(
            self._line(partner_id=self.salinas.id)._retrieve_partner(), self.salinas
        )
        line = self._line(partner_id=self.holder.id)
        self.assertEqual(
            line.with_context(skip_retrieve_partner=True)._retrieve_partner(),
            self.holder,
        )
        self.assertEqual(line.partner_id, self.holder)

    def test_conflicting_models_return_empty(self):
        self._mapping(self.salinas, r"(?i).*TEMPLAGLASS.*", name="Conflicting mapping")
        self.assertFalse(self._line()._retrieve_partner())

    def test_model_applicability_filters(self):
        self.templa_model.match_amount = "greater"
        self.templa_model.match_amount_min = 100
        self.assertFalse(self._line()._retrieve_partner())
        self.templa_model.match_amount = False
        self.templa_model.match_nature = "amount_received"
        self.assertFalse(self._line()._retrieve_partner())
        self.templa_model.match_nature = "amount_paid"
        self.templa_model.match_journal_ids = [
            Command.set(self.company_data["default_journal_bank"].ids)
        ]
        self.assertFalse(self._line()._retrieve_partner())

    def test_other_company_mapping_is_ignored(self):
        other_company = self.setup_other_company()["company"]
        other = self._mapping(
            self.salinas, r"(?i).*TEMPLAGLASS.*", name="Other company"
        )
        other.write(
            {
                "match_journal_ids": [Command.clear()],
                "company_id": other_company.id,
            }
        )
        self.assertEqual(self._line()._retrieve_partner(), self.templa)

    def test_missing_structured_record_never_uses_legacy(self):
        self.bank.n43_allow_legacy_lines = True
        self.assertFalse(self._line(n43_complementary_concepts={})._retrieve_partner())

    def test_holder_commercial_contact(self):
        child = self.env["res.partner"].create(
            {"name": "Holder contact", "parent_id": self.holder.id}
        )
        self.assertEqual(
            self._line(partner_id=child.id)._retrieve_partner(), self.templa
        )

    def test_company_holder_is_automatic(self):
        self.bank.n43_ignored_partner_ids = [Command.clear()]
        line = self._line(
            partner_id=self.company.partner_id.id,
            partner_name=self.company.partner_id.name,
        )
        self.assertEqual(line._retrieve_partner(), self.templa)

    def test_holder_bank_account(self):
        bank = self.env["res.partner.bank"].create(
            {"partner_id": self.holder.id, "acc_number": "ES1234567890"}
        )
        line = self._line(account_number=bank.acc_number)
        self.assertEqual(line._retrieve_partner(), self.templa)

    def test_other_payment_types_keep_upstream(self):
        for label in ("CARD TEMPLAGLASS", "REFUND TEMPLAGLASS", "CORETGSS CASHFra.1"):
            with self.subTest(label=label):
                line = self._line(payment_ref=label)
                self.assertEqual(line._retrieve_partner(), self.holder)

    def test_custom_record_and_outgoing_marker(self):
        self.bank.write(
            {"n43_beneficiary_record": "04", "n43_outgoing_patterns": "Bank transfer"}
        )
        line = self._line(
            payment_ref="Bank transfer TEMPLAGLASS",
            n43_complementary_concepts={"04": ["TEMPLAGLASS", "SL"]},
        )
        self.assertEqual(line._retrieve_partner(), self.templa)

    def test_missing_partner_blocks_supplier_suggestion(self):
        self._outstanding(self.miexal)
        line = self._line(beneficiary="UNKNOWN SUPPLIER")
        self.assertFalse(line._retrieve_partner())
        self.assertFalse(self.templa_model._apply_rules(line, line._retrieve_partner()))

    def test_invalid_extraction_pattern(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.bank.n43_legacy_beneficiary_regex = "["
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.bank.n43_legacy_beneficiary_regex = ".*"

    def test_n43_import_preserves_concepts_and_partner_search_modes(self):
        wizard = self.env["account.statement.import"].create({})
        raw = {
            "conceptos": {
                "01": (self.holder.name, ""),
                "02": ("48353047D", ""),
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
        for mode in ("none", "all"):
            with self.subTest(mode=mode):
                self.bank.n43_partner_search = mode
                parsed = wizard._parse_single_file_n43([group])
                completed = wizard._complete_stmts_vals(parsed[2], self.bank, parsed[1])
                vals = completed[0]["transactions"][0]
                self.assertEqual(vals["n43_complementary_concepts"], raw["conceptos"])
                self.assertEqual(vals["partner_name"], self.holder.name)
                self.assertIn("48353047D", vals["payment_ref"])
                self.assertNotIn("n43_line", vals)
                if mode == "none":
                    self.assertFalse(vals["partner_id"])
                line = (
                    self.env["account.bank.statement.line"]
                    .with_context(skip_retrieve_partner=True)
                    .create(vals)
                    .with_context(skip_retrieve_partner=False)
                )
                self.assertEqual(line._retrieve_partner(), self.templa)
