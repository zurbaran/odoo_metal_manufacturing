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
        """Find a unique partner using Odoo 19's mapping models.

        Odoo 19 replaces partner_mapping_line_ids with mapped_partner_id,
        computed on models that have exactly one partner-only rule line.
        """
        self.ensure_one()
        partners = self.env["res.partner"]
        holders = self._n43_account_holders()
        models = self.env["account.reconcile.model"].search(
            [
                ("active", "=", True),
                ("company_id", "=", self.company_id.id),
                ("mapped_partner_id", "!=", False),
                ("match_label", "in", ["contains", "match_regex"]),
            ]
        )
        for model in models:
            partner = model.mapped_partner_id
            if (
                partner.commercial_partner_id in holders
                or (partner.company_id and partner.company_id != self.company_id)
                or (model.match_journal_ids and self.journal_id not in model.match_journal_ids)
                or (model.match_partner_ids and partner not in model.match_partner_ids)
            ):
                continue
            if model.match_amount == "lower" and self.amount > model.match_amount_max:
                continue
            if model.match_amount == "greater" and self.amount < model.match_amount_min:
                continue
            if model.match_amount == "between" and not (
                model.match_amount_max <= self.amount <= model.match_amount_min
            ):
                continue
            pattern = model.match_label_param or ""
            if not pattern:
                continue
            if model.match_label == "contains":
                matches = pattern.casefold() in beneficiary.casefold()
            else:
                matches = bool(re.search(pattern, beneficiary, re.IGNORECASE))
            if matches:
                partners |= partner
        return partners if len(partners) == 1 else self.env["res.partner"]

    def _n43_resolved_partner(self):
        """Never replace an identified non-holder with a beneficiary guess."""
        self.ensure_one()
        partner = self.partner_id
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

    def _retrieve_partner(self):
        """Odoo 19 writes partner_id directly and supports record batches."""
        result = super()._retrieve_partner()
        if self.env.context.get("skip_retrieve_partner"):
            return result
        for line in self:
            if not line._n43_is_outgoing_transfer():
                continue
            resolved = line._n43_resolved_partner()
            if resolved != line.partner_id:
                line.partner_id = resolved
        return result
