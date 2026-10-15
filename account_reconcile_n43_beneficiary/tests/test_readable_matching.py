# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..utils.text_matching import matches, simple_prefix


@tagged("post_install", "-at_install")
class TestReadableMatching(AccountTestInvoicingCommon):
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
                "rule_type": "invoice_matching",
                "auto_reconcile": False,
                "match_nature": "amount_paid",
                "match_partner": True,
                "match_partner_ids": [Command.set([cls.partner_a.id])],
                "match_journal_ids": [Command.set([cls.bank.id])],
                "partner_mapping_line_ids": [
                    Command.create(
                        {
                            "partner_id": cls.partner_a.id,
                            "n43_match_type": "starts_with",
                            "n43_text": "COREMUTUA",
                        }
                    )
                ],
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

    def test_literal_operations_and_casing(self):
        cases = [
            ("starts_with", "Core", "CORE x", True),
            ("starts_with", "Core", "x CORE", False),
            ("contains", "Core", "x CORE x", True),
            ("ends_with", "Core", "x CORE", True),
            ("ends_with", "Core", "CORE x", False),
            ("exact", "Core", "CORE", True),
            ("exact", "Core", "CORE x", False),
            ("exact", "Core", "CORE\n", False),
            ("contains", "[A]._%", "x [a]._% x", True),
            ("contains", "[A]._%", "A anything", False),
            ("exact", "Í", "í", True),
        ]
        for kind, pattern, value, expected in cases:
            with self.subTest(kind=kind, value=value):
                self.assertEqual(matches(kind, pattern, value), expected)
        self.assertFalse(matches("starts_with", "Core", "CORE", True))
        self.assertTrue(matches("regex", r"(?i)^core\d+", "CORE123"))
        self.assertFalse(matches("regex", r"core", "x core"))

    def test_core_mapping_and_anchor(self):
        self.assertEqual(
            self._line("coremutua receipt")._retrieve_partner(), self.partner_a
        )
        self.assertFalse(
            self.model._get_partner_from_mapping(self._line("x COREMUTUA"))
        )
        self.assertFalse(self._line()._n43_is_outgoing_transfer())

    def test_ambiguous_mappings_in_one_model(self):
        self.model.write(
            {
                "partner_mapping_line_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner_b.id,
                            "n43_match_type": "contains",
                            "n43_text": "COREMUTUA",
                        }
                    )
                ],
                "match_partner_ids": [Command.clear()],
            }
        )
        self.assertFalse(self.model._get_partner_from_mapping(self._line()))
        self.assertFalse(self._line()._retrieve_partner())

    def test_ambiguous_models(self):
        self.model.copy(
            {
                "name": "Conflicting readable rule",
                "match_partner_ids": [Command.set([self.partner_b.id])],
                "partner_mapping_line_ids": [
                    Command.clear(),
                    Command.create(
                        {
                            "partner_id": self.partner_b.id,
                            "n43_match_type": "starts_with",
                            "n43_text": "CORE",
                        }
                    ),
                ],
            }
        )
        self.assertFalse(self._line()._retrieve_partner())

    def test_bank_account_disagreement_is_ambiguous(self):
        self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner_b.id,
                "acc_number": "N43ACCOUNT",
            }
        )
        self.assertFalse(self._line(account_number="N43ACCOUNT")._retrieve_partner())
        self.assertEqual(
            self._line(partner_id=self.partner_b.id)._retrieve_partner(), self.partner_b
        )

    def test_full_model_restrictions(self):
        self.model.write(
            {
                "n43_label_match_type": "starts_with",
                "n43_label_text": "COREMUTUA",
                "match_amount": "between",
                "match_amount_min": 10,
                "match_amount_max": 30,
            }
        )
        line = self._line()
        self.assertTrue(self.model._is_applicable_for(line, self.partner_a))
        self.assertFalse(self.model._is_applicable_for(line, self.partner_b))
        self.assertFalse(
            self.model._is_applicable_for(self._line(amount=-31), self.partner_a)
        )
        self.assertFalse(
            self.model._is_applicable_for(self._line(amount=25), self.partner_a)
        )
        self.assertFalse(
            self.model._is_applicable_for(self._line("x COREMUTUA"), self.partner_a)
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
            self.model._is_applicable_for(
                self._line(journal_id=other.id), self.partner_a
            )
        )
        self.assertFalse(self.model.auto_reconcile)

    def test_n43_beneficiary_and_original_data(self):
        self.model.partner_mapping_line_ids.write(
            {
                "n43_match_type": "contains",
                "n43_text": "TEMPLAGLASS",
            }
        )
        line = self._line(
            "Holder CASHFra.261870 TEMPLAGLASS SL",
            partner_id=self.company.partner_id.id,
            n43_imported=True,
            n43_complementary_concepts={"05": ["TEMPLAGLASS SL", ""]},
        )
        before = line.read(["payment_ref", "partner_id", "n43_complementary_concepts"])
        self.assertEqual(line._retrieve_partner(), self.partner_a)
        self.assertEqual(
            before,
            line.read(["payment_ref", "partner_id", "n43_complementary_concepts"]),
        )

    def test_safe_conversion_roundtrip_and_snapshot(self):
        pattern = "^" + "".join("[" + c + c.lower() + "]" for c in "COREDIGI") + ".*"
        self.model.write({"match_label": "match_regex", "match_label_param": pattern})
        mapping = self.model.partner_mapping_line_ids
        mapping.write({"n43_match_type": False, "payment_ref_regex": pattern})
        self.model.action_n43_simplify()
        self.assertEqual(self.model.n43_label_text, "COREDIGI")
        self.assertEqual(mapping.n43_text, "COREDIGI")
        self.assertFalse(self.model._get_partner_from_mapping(self._line("COREDİGİ")))
        self.assertTrue(self.model._get_partner_from_mapping(self._line("coredigi")))
        self.env.flush_all()
        self.cr.execute(
            "SELECT n43_migration_config FROM account_reconcile_model WHERE id=%s",
            [self.model.id],
        )
        snapshot = self.cr.fetchone()[0]
        self.assertEqual(snapshot["label_rule"]["kind"], "starts_with")
        self.assertFalse(snapshot["auto_reconcile"])
        self.model.write({"n43_label_match_type": False})
        mapping.write({"n43_match_type": False})
        self.assertEqual(self.model.match_label_param, pattern)
        self.assertEqual(mapping.payment_ref_regex, pattern)

    def test_unrecognized_expression_is_retained(self):
        pattern = r"(?i)^COREEMP\..*(?:CALPE|CA\s+LPE).*"
        self.model.partner_mapping_line_ids.write(
            {"n43_match_type": False, "payment_ref_regex": pattern}
        )
        self.model.action_n43_simplify()
        self.assertEqual(self.model.partner_mapping_line_ids.payment_ref_regex, pattern)
        self.assertFalse(self.model.partner_mapping_line_ids.n43_match_type)
        self.assertIsNone(simple_prefix(pattern))

    def test_literal_not_regex_and_invalid_advanced(self):
        mapping = self.model.partner_mapping_line_ids
        mapping.write({"n43_match_type": "exact", "n43_text": "["})
        self.assertEqual(
            self.model._get_partner_from_mapping(self._line("[")), self.partner_a
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            mapping.write({"n43_match_type": "regex", "n43_text": "["})

    def test_existing_python_regex_keeps_match_semantics(self):
        mapping = self.model.partner_mapping_line_ids
        mapping.write({"n43_match_type": False, "payment_ref_regex": r"(?i)CORE\b"})
        self.assertEqual(
            self.model._get_partner_from_mapping(self._line("core receipt")),
            self.partner_a,
        )
        self.assertFalse(
            self.model._get_partner_from_mapping(self._line("x core receipt"))
        )

    def test_prefix_parser_does_not_guess(self):
        for pattern in [r".*CORE", r"^CORE$", r"^CORE\s+", r"^CORE(A|B)", r"[Cc]ore.*"]:
            self.assertIsNone(simple_prefix(pattern))
        self.assertEqual(simple_prefix(r"(?i)^COREMUTUA.*")[:2], ("COREMUTUA", False))
        self.assertTrue(re.match(r"(?i)^COREMUTUA.*", "coremutua"))

    def test_model_conversion_keeps_unicode_flag_semantics(self):
        self.model.write(
            {"match_label": "match_regex", "match_label_param": "(?i)^CORES.*"}
        )
        line = self._line("COREſ receipt")
        self.assertTrue(self.model._is_applicable_for(line, self.partner_a))
        self.model.action_n43_simplify()
        self.assertTrue(self.model._is_applicable_for(line, self.partner_a))
