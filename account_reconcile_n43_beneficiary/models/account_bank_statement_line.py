# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
import unicodedata

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    n43_imported = fields.Boolean(string="Imported from N43", readonly=True, copy=False)
    n43_complementary_concepts = fields.Json(
        string="Original N43 Concept Details",
        readonly=True,
        copy=False,
        help="Additional copy of parsed N43 concept records. Original bank fields "
        "are preserved.",
    )

    def _n43_account_holders(self):
        self.ensure_one()
        return (
            self.company_id.partner_id | self.journal_id.n43_ignored_partner_ids
        ).commercial_partner_id

    @staticmethod
    def _n43_normalize_name(value):
        normalized = unicodedata.normalize("NFKD", value or "")
        return " ".join(
            re.findall(
                r"\w+", "".join(c for c in normalized if not unicodedata.combining(c))
            )
        ).casefold()

    def _n43_is_holder_name(self, name):
        normalized = self._n43_normalize_name(name)
        return bool(normalized) and any(
            normalized == self._n43_normalize_name(partner.name)
            for partner in (
                self._n43_account_holders() | self.journal_id.n43_ignored_partner_ids
            )
        )

    def _n43_is_outgoing_transfer(self):
        self.ensure_one()
        journal = self.journal_id
        label = self.payment_ref or ""
        return (
            journal.type == "bank"
            and journal.n43_beneficiary_enabled
            and self.amount < 0
            and not self.is_reconciled
            and (self.n43_imported or journal.n43_allow_legacy_lines)
            and not re.search(r"\bCORE", label, re.IGNORECASE)
            and any(
                marker.strip().casefold() in label.casefold()
                for marker in (journal.n43_outgoing_patterns or "").splitlines()
                if marker.strip()
            )
        )

    def _n43_beneficiary_text(self):
        """Use structured concepts first; never fall back if that record is missing."""
        self.ensure_one()
        concepts = self.n43_complementary_concepts or {}
        if self.n43_imported:
            parts = concepts.get(self.journal_id.n43_beneficiary_record, [])
            return " ".join(part.strip() for part in parts if part.strip())
        pattern = self.journal_id.n43_legacy_beneficiary_regex
        match = re.search(pattern, self.payment_ref or "") if pattern else None
        return (match.group("beneficiary") or "").strip() if match else ""

    def _n43_partner_from_beneficiary_mappings(self, beneficiary):
        """Reuse OCA mappings on beneficiary text and applicability on the real line."""
        self.ensure_one()
        partners = self.env["res.partner"]
        # In-memory record only: no bank data, move or partner is written.
        beneficiary_line = self.new(
            {"payment_ref": beneficiary, "narration": beneficiary}
        )
        models = self.env["account.reconcile.model"].search(
            [
                ("rule_type", "!=", "writeoff_button"),
                ("company_id", "=", self.company_id.id),
            ]
        )
        holders = self._n43_account_holders()
        for model in models:
            partner = model._get_partner_from_mapping(beneficiary_line)
            if (
                partner
                and partner.commercial_partner_id not in holders
                and (not partner.company_id or partner.company_id == self.company_id)
                and model._is_applicable_for(self, partner)
            ):
                partners |= partner
        # Conflicting mappings must be reviewed rather than resolved by sequence.
        return partners if len(partners) == 1 else self.env["res.partner"]

    def _retrieve_partner(self):
        self.ensure_one()
        if self.env.context.get("skip_retrieve_partner"):
            return self.partner_id
        partner = super()._retrieve_partner()
        if not self._n43_is_outgoing_transfer():
            return partner
        if partner and partner.commercial_partner_id not in self._n43_account_holders():
            return partner
        if not partner and not self._n43_is_holder_name(self.partner_name):
            return partner
        beneficiary = self._n43_beneficiary_text()
        if not any(char.isalpha() for char in beneficiary) or self._n43_is_holder_name(
            beneficiary
        ):
            return self.env["res.partner"]
        return self._n43_partner_from_beneficiary_mappings(beneficiary)
