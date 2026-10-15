# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.extras import Json

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..hooks import migrate_18_mappings, preserve_19_mappings
from ..utils.text_matching import matches


@tagged("post_install", "-at_install")
class TestReadableMatching19(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.env["account.reconcile.model"].search(
            [("company_id", "=", cls.company.id)]
        ).active = False
        cls.bank = cls.env["account.journal"].create(
            {
                "name": "Readable N43",
                "code": "R43",
                "type": "bank",
                "company_id": cls.company.id,
                "n43_beneficiary_enabled": True,
            }
        )
        cls.partner_a = cls.env["res.partner"].create({"name": "Supplier A"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Supplier B"})
        cls.model = cls.env["account.reconcile.model"].create(
            {
                "name": "Readable supplier",
                "company_id": cls.company.id,
                "trigger": "manual",
                "match_journal_ids": [Command.set([cls.bank.id])],
                "n43_match_type": "starts_with",
                "n43_text": "COREMUTUA",
                "line_ids": [Command.create({"partner_id": cls.partner_a.id})],
            }
        )

    def _line(self, label="COREMUTUA receipt", **extra):
        return (
            self.env["account.bank.statement.line"]
            .with_context(skip_retrieve_partner=True)
            .create(
                {
                    "journal_id": self.bank.id,
                    "date": fields.Date.today(),
                    "amount": -25,
                    "payment_ref": label,
                    **extra,
                }
            )
            .with_context(skip_retrieve_partner=False)
        )

    def test_operations_casing_and_exact_boundaries(self):
        for kind, text, value, expected in [
            ("starts_with", "CORE", "core x", True),
            ("starts_with", "CORE", "x core", False),
            ("contains", "CORE", "x core x", True),
            ("ends_with", "CORE", "x core", True),
            ("ends_with", "CORE", "core x", False),
            ("exact", "CORE", "core", True),
            ("exact", "CORE", "core\n", False),
            ("contains", "[A]._%", "x [a]._% x", True),
            ("contains", "[A]._%", "A anything", False),
            ("exact", "Í", "í", True),
        ]:
            with self.subTest(kind=kind, value=value):
                self.assertEqual(matches(kind, text, value), expected)
        self.assertFalse(matches("starts_with", "CORE", "core", True))

    def test_core_resolution_and_anchor(self):
        line = self._line("coremutua receipt")
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.partner_a)
        self.assertFalse(line._n43_is_outgoing_transfer())
        line = self._line("prefix COREMUTUA")
        line._retrieve_partner()
        self.assertFalse(line.partner_id)
        self.assertEqual(self.model.trigger, "manual")

    def test_core_import_resolves_before_create_with_skip_context(self):
        wizard = self.env["account.statement.import"].create({})
        raw = {
            "conceptos": {"01": ("COREMUTUA receipt", ""), "05": ("Bank text", "")},
            "importe": -25,
            "referencia1": "",
            "referencia2": "",
            "fecha_valor": fields.Date.today(),
            "fecha_oper": fields.Date.today(),
        }
        parsed = wizard._parse_single_file_n43(
            [
                {
                    "lines": [raw],
                    "saldo_ini": 100,
                    "saldo_fin": 75,
                    "divisa": "978",
                    "cuenta": "1234567890",
                }
            ]
        )
        values = wizard._complete_stmts_vals(parsed[2], self.bank, parsed[1])
        transaction = values[0]["transactions"][0]
        self.assertEqual(transaction["partner_id"], self.partner_a.id)
        self.assertIn("COREMUTUA", transaction["payment_ref"])
        self.assertEqual(transaction["amount"], -25)

    def test_conflicts_return_no_partner(self):
        self.model.copy(
            {
                "name": "Conflicting CORE",
                "n43_text": "CORE",
                "line_ids": [
                    Command.clear(),
                    Command.create({"partner_id": self.partner_b.id}),
                ],
            }
        )
        line = self._line()
        line._retrieve_partner()
        self.assertFalse(line.partner_id)

    def test_signed_amount_and_journal_filters(self):
        self.model.write(
            {
                "match_amount": "between",
                "match_amount_max": -30,
                "match_amount_min": -10,
            }
        )
        self.assertTrue(self.model._n43_conditions_apply(self._line(), self.partner_a))
        self.assertFalse(
            self.model._n43_conditions_apply(self._line(amount=-31), self.partner_a)
        )
        self.assertFalse(
            self.model._n43_conditions_apply(self._line(amount=25), self.partner_a)
        )
        other = self.env["account.journal"].create(
            {
                "name": "Other bank",
                "code": "R44",
                "type": "bank",
                "company_id": self.company.id,
            }
        )
        self.assertFalse(
            self.model._n43_conditions_apply(
                self._line(journal_id=other.id), self.partner_a
            )
        )
        self.model.match_partner_ids = [Command.set([self.partner_b.id])]
        self.assertFalse(self.model._n43_conditions_apply(self._line(), self.partner_a))

    def test_bank_account_disagreement_is_ambiguous(self):
        self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner_b.id,
                "acc_number": "N43ACCOUNT",
            }
        )
        line = self._line(account_number="N43ACCOUNT")
        line._retrieve_partner()
        self.assertFalse(line.partner_id)
        line = self._line(partner_id=self.partner_b.id)
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.partner_b)

    def test_other_company_mapping_is_not_used(self):
        company = self.env["res.company"].create({"name": "Other readable company"})
        self.model.copy(
            {
                "name": "Other company CORE",
                "company_id": company.id,
                "match_journal_ids": [Command.clear()],
                "line_ids": [
                    Command.clear(),
                    Command.create({"partner_id": self.partner_b.id}),
                ],
            }
        )
        line = self._line()
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.partner_a)

    def test_n43_preserves_original_concepts(self):
        self.model.write({"n43_match_type": "contains", "n43_text": "TEMPLAGLASS"})
        line = self._line(
            "Holder CASHFra.261870 TEMPLAGLASS SL",
            partner_id=self.company.partner_id.id,
            n43_imported=True,
            n43_complementary_concepts={"05": ["TEMPLAGLASS SL", ""]},
        )
        before = line.read(
            ["payment_ref", "partner_name", "n43_complementary_concepts"]
        )
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.partner_a)
        self.assertEqual(
            before,
            line.read(["payment_ref", "partner_name", "n43_complementary_concepts"]),
        )
        self.assertFalse(line.is_reconciled)

    def test_backend_sql_uses_literal_options(self):
        model = self.env["account.reconcile.model"].create(
            {
                "name": "Literal proposal",
                "company_id": self.company.id,
                "trigger": "manual",
                "n43_label_match_type": "exact",
                "n43_label_text": "CORE[A]._%",
                "n43_label_case_sensitive": True,
                "line_ids": [
                    Command.create(
                        {"account_id": self.company_data["default_account_expense"].id}
                    )
                ],
            }
        )
        good = self._line("CORE[A]._%")
        bad = self._line("core[A]._%")
        partial = self._line("prefix CORE[A]._%")
        result = model._get_rules(good | bad | partial, trigger="manual")
        self.assertIn(model.id, result.get(good.id, []))
        self.assertNotIn(model.id, result.get(bad.id, []))
        self.assertNotIn(model.id, result.get(partial.id, []))

    def _proposal_mapping(self, partner, text, **extra):
        model = self.model.copy(
            {
                "name": "Proposal: " + partner.name,
                "n43_text": text,
                "line_ids": [
                    Command.clear(),
                    Command.create({"partner_id": partner.id}),
                ],
                **extra,
            }
        )
        self.assertFalse(model.can_be_proposed)
        # Editing a child counterpart can make a former partner-only rule
        # proposable without clearing its readable identification criterion.
        model.line_ids.account_id = self.company_data["default_account_expense"]
        self.assertFalse(model.mapped_partner_id)
        self.assertTrue(model.can_be_proposed)
        return model

    def test_partner_only_mapping_models_are_not_proposed(self):
        line = self._line()
        self.assertFalse(self.model.can_be_proposed)
        self.assertNotIn(
            self.model.id,
            self.model._get_rules(line, trigger="manual").get(line.id, []),
        )

    def test_mapping_only_proposals_do_not_cross_suppliers(self):
        model_a = self._proposal_mapping(self.partner_a, "COREMUTUA")
        model_b = self._proposal_mapping(self.partner_b, "COREDIGI")
        unmanaged = self.env["account.reconcile.model"].create(
            {
                "name": "Native proposal",
                "company_id": self.company.id,
                "trigger": "manual",
                "match_label": "contains",
                "match_label_param": "receipt",
                "line_ids": [
                    Command.create(
                        {"account_id": self.company_data["default_account_expense"].id}
                    )
                ],
            }
        )
        line_a = self._line("coremutua receipt")
        line_b = self._line("COREDIGI receipt")
        unknown = self._line("Unknown receipt")
        unanchored = self._line("prefix COREMUTUA receipt")
        result = self.model._get_rules(
            line_a | line_b | unknown | unanchored, trigger="manual"
        )
        for line, expected, other in [
            (line_a, model_a, model_b),
            (line_b, model_b, model_a),
        ]:
            self.assertIn(expected.id, result.get(line.id, []))
            self.assertNotIn(other.id, result.get(line.id, []))
        for line in (unknown, unanchored):
            self.assertNotIn(model_a.id, result.get(line.id, []))
            self.assertNotIn(model_b.id, result.get(line.id, []))
        for line in (line_a, line_b, unknown, unanchored):
            self.assertIn(unmanaged.id, result.get(line.id, []))

    def test_mapping_proposals_also_check_existing_managed_conditions(self):
        for extra in (
            {"n43_label_match_type": "starts_with", "n43_label_text": "CORE"},
            {"n43_source_conditions": {"match_nature": "amount_paid"}},
        ):
            with self.subTest(extra=extra):
                model_a = self._proposal_mapping(self.partner_a, "COREMUTUA", **extra)
                model_b = self._proposal_mapping(self.partner_b, "COREDIGI", **extra)
                line = self._line()
                result = self.model._get_rules(line, trigger="manual")
                self.assertIn(model_a.id, result.get(line.id, []))
                self.assertNotIn(model_b.id, result.get(line.id, []))

    def test_mapping_proposals_use_extracted_transfer_beneficiary(self):
        model_a = self._proposal_mapping(
            self.partner_a, "Supplier A", n43_match_type="exact"
        )
        model_b = self._proposal_mapping(
            self.partner_b, "Supplier B", n43_match_type="exact"
        )
        line_a = self._line(
            "Supplier B CASHFra.TEST Supplier A",
            n43_imported=True,
            n43_complementary_concepts={"05": ["Supplier A", ""]},
        )
        line_b = self._line(
            "Supplier A CASHFra.TEST Supplier B",
            n43_imported=True,
            n43_complementary_concepts={"05": ["Supplier B", ""]},
        )
        missing = self._line("Supplier A CASHFra.TEST", n43_imported=True)
        self.bank.n43_allow_legacy_lines = True
        legacy = self._line("Holder CASHFra.TEST Supplier A")
        result = self.model._get_rules(
            line_a | line_b | missing | legacy, trigger="manual"
        )
        for line, expected, other in [
            (line_a, model_a, model_b),
            (line_b, model_b, model_a),
        ]:
            self.assertIn(expected.id, result.get(line.id, []))
            self.assertNotIn(other.id, result.get(line.id, []))
        self.assertNotIn(model_a.id, result.get(missing.id, []))
        self.assertNotIn(model_b.id, result.get(missing.id, []))
        self.assertIn(model_a.id, result.get(legacy.id, []))
        self.assertNotIn(model_b.id, result.get(legacy.id, []))

    def test_mapping_proposals_use_full_core_label(self):
        model_a = self._proposal_mapping(self.partner_a, "COREMUTUA")
        model_b = self._proposal_mapping(self.partner_b, "COREDIGI")
        line_a = self._line(
            "COREMUTUA receipt CASHFra.TEST",
            n43_imported=True,
            n43_complementary_concepts={"05": ["COREDIGI", ""]},
        )
        line_b = self._line(
            "coredigi receipt CASHFra.TEST",
            n43_imported=True,
            n43_complementary_concepts={"05": ["COREMUTUA", ""]},
        )
        self.assertFalse(line_a._n43_is_outgoing_transfer())
        self.assertFalse(line_b._n43_is_outgoing_transfer())
        result = self.model._get_rules(line_a | line_b, trigger="manual")
        self.assertIn(model_a.id, result.get(line_a.id, []))
        self.assertNotIn(model_b.id, result.get(line_a.id, []))
        self.assertIn(model_b.id, result.get(line_b.id, []))
        self.assertNotIn(model_a.id, result.get(line_b.id, []))

    def test_mapping_proposal_restrictions_are_preserved(self):
        model = self._proposal_mapping(
            self.partner_a,
            "COREMUTUA",
            match_partner_ids=[Command.set([self.partner_a.id])],
            match_amount="between",
            match_amount_max=-30,
            match_amount_min=-10,
        )
        other_bank = self.env["account.journal"].create(
            {
                "name": "Other proposal bank",
                "code": "RP2",
                "type": "bank",
                "company_id": self.company.id,
            }
        )
        good = self._line(partner_id=self.partner_a.id)
        wrong_partner = self._line(partner_id=self.partner_b.id)
        wrong_amount = self._line(amount=-31, partner_id=self.partner_a.id)
        wrong_journal = self._line(
            journal_id=other_bank.id, partner_id=self.partner_a.id
        )
        result = self.model._get_rules(
            good | wrong_partner | wrong_amount | wrong_journal, trigger="manual"
        )
        self.assertIn(model.id, result.get(good.id, []))
        for line in (wrong_partner, wrong_amount, wrong_journal):
            self.assertNotIn(model.id, result.get(line.id, []))
        self.assertEqual(model.trigger, "manual")

    def test_mapping_proposals_respect_company(self):
        model = self._proposal_mapping(
            self.partner_a, "COREMUTUA", match_journal_ids=[Command.clear()]
        )
        other = self.setup_other_company(name="Other proposal company")
        good = self._line()
        foreign = self._line(
            journal_id=other["default_journal_bank"].id,
            company_id=other["company"].id,
        )
        result = self.model._get_rules(good | foreign, trigger="manual")
        self.assertIn(model.id, result.get(good.id, []))
        self.assertNotIn(model.id, result.get(foreign.id, []))

    def test_advanced_python_never_reaches_postgresql(self):
        self.model.write({"n43_match_type": "regex", "n43_text": r"(?i:coremutua)\b"})
        self.assertEqual(self.model.match_label_param, ".*")
        line = self._line()
        line._retrieve_partner()
        self.assertEqual(line.partner_id, self.partner_a)
        line = self._line("x coremutua")
        line._retrieve_partner()
        self.assertFalse(line.partner_id)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.model.write({"n43_text": "["})

    @mute_logger("odoo.sql_db")
    def test_native_regex_is_checked_in_both_engines(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["account.reconcile.model"].create(
                {
                    "name": "Nonportable native regex",
                    "match_label": "match_regex",
                    "match_label_param": r"(?i:CORE)",
                }
            )
        self.cr.execute("SELECT %s ~* %s", ["COREMUTUA", "(?i)^COREMUTUA.*"])
        self.assertTrue(self.cr.fetchone()[0])

    def test_19_upgrade_preserves_previous_search_semantics(self):
        model = self.env["account.reconcile.model"].create(
            {
                "name": "Previous 19 port",
                "match_label": "match_regex",
                "match_label_param": "TEMPlA",
                "trigger": "manual",
                "line_ids": [Command.create({"partner_id": self.partner_b.id})],
            }
        )
        preserve_19_mappings(self.env)
        self.assertTrue(model._n43_mapping_matches("prefix templa suffix"))
        self.assertEqual(model.n43_match_legacy["match_label_param"], "TEMPlA")

    def test_19_upgrade_preserves_contains_casefold(self):
        model = self.env["account.reconcile.model"].create(
            {
                "name": "Previous 19 contains",
                "match_label": "contains",
                "match_label_param": "STRASSE",
                "line_ids": [Command.create({"partner_id": self.partner_b.id})],
            }
        )
        preserve_19_mappings(self.env)
        self.assertTrue(model._n43_mapping_matches("Straße"))
        self.assertEqual(model.trigger, "manual")
        preserve_19_mappings(self.env)
        self.assertEqual(model.n43_match_legacy["match_label_param"], "STRASSE")

    def test_18_migration_recovers_scopes_and_restrictions(self):
        source = self.env["account.reconcile.model"].create(
            {
                "name": "Original 18 rule",
                "active": False,
                "match_journal_ids": [Command.set([self.bank.id])],
                "n43_migration_config": {
                    "active": True,
                    "auto_reconcile": False,
                    "match_nature": "amount_paid",
                    "match_amount": "between",
                    "match_amount_min": 10,
                    "match_amount_max": 30,
                    "match_label": "match_regex",
                    "match_label_param": "^CORE",
                    "match_partner": True,
                    "match_partner_ids": [self.partner_a.id],
                },
            }
        )
        target = source.copy(
            {
                "name": "OU partner mapping",
                "match_label": "contains",
                "match_label_param": "CORE",
                "trigger": "manual",
                "line_ids": [Command.create({"partner_id": self.partner_a.id})],
            }
        )
        self.cr.execute("""
            CREATE TABLE account_reconcile_model_partner_mapping (
                id integer PRIMARY KEY, model_id integer, partner_id integer,
                payment_ref_regex varchar, narration_regex varchar,
                n43_migration_config jsonb
            )
        """)
        self.cr.execute("""
            ALTER TABLE account_reconcile_model
            ADD COLUMN openupgrade_legacy_19_0_partner_mapping_id integer
        """)
        self.cr.execute(
            """
            INSERT INTO account_reconcile_model_partner_mapping
            VALUES (90001, %s, %s, %s, %s, %s)
        """,
            [
                source.id,
                self.partner_a.id,
                "(?i)^COREMUTUA",
                "^approved",
                Json(
                    {
                        "kind": "starts_with",
                        "text": "COREMUTUA",
                        "case_sensitive": False,
                        "narration_regex": "^approved",
                    }
                ),
            ],
        )
        self.env.flush_all()
        self.cr.execute(
            """
            UPDATE account_reconcile_model
            SET openupgrade_legacy_19_0_partner_mapping_id = 90001 WHERE id=%s
        """,
            [target.id],
        )
        migrate_18_mappings(self.env)
        self.assertTrue(target.active)
        self.assertEqual(target.trigger, "manual")
        self.assertEqual(target.n43_source_mapping_id, 90001)
        self.assertTrue(target._n43_mapping_matches("coremutua receipt", "approved"))
        self.assertFalse(target._n43_mapping_matches("prefix coremutua", "approved"))
        self.assertFalse(target._n43_mapping_matches("COREMUTUA", "wrong note"))
        self.assertTrue(target._n43_conditions_apply(self._line(), self.partner_a))
        self.assertFalse(
            target._n43_conditions_apply(self._line(amount=-30.01), self.partner_a)
        )
        self.assertFalse(
            target._n43_conditions_apply(self._line(amount=25), self.partner_a)
        )
        self.assertEqual(
            target.n43_match_legacy["source_mapping"]["payment_ref_regex"],
            "(?i)^COREMUTUA",
        )
        migrate_18_mappings(self.env)
        self.assertEqual(target.n43_source_mapping_id, 90001)
        self.cr.execute("SELECT COUNT(*) FROM account_reconcile_model_partner_mapping")
        self.assertEqual(self.cr.fetchone()[0], 1)
        # Editing the native filters later must not leave a hidden stale copy.
        target.write({"match_amount": "lower", "match_amount_max": -100})
        self.assertTrue(
            target._n43_conditions_apply(self._line(amount=-150), self.partner_a)
        )
        self.assertEqual(
            target.n43_match_legacy["source_conditions"]["match_amount_max"], 30
        )
        target.write({"n43_label_match_type": "starts_with", "n43_label_text": "OTHER"})
        self.assertTrue(
            target._n43_conditions_apply(
                self._line("OTHER", amount=-150), self.partner_a
            )
        )

    def test_simple_prefix_conversion_keeps_anchor(self):
        self.model.write(
            {
                "n43_match_type": "regex",
                "n43_text": "(?i)^COREMUTUA.*",
            }
        )
        self.model.action_n43_simplify()
        self.assertEqual(self.model.n43_match_type, "starts_with")
        self.assertTrue(self.model._n43_mapping_matches("coremutua receipt"))
        self.assertFalse(self.model._n43_mapping_matches("prefix coremutua"))
