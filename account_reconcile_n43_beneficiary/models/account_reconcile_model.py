# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext

from ..utils.text_matching import MATCH_TYPES, matches, simple_prefix

CONDITION_FIELDS = [
    "active",
    "auto_reconcile",
    "match_nature",
    "match_amount",
    "match_amount_min",
    "match_amount_max",
    "match_label",
    "match_label_param",
    "match_note",
    "match_note_param",
    "match_transaction_type",
    "match_transaction_type_param",
    "match_partner",
    "match_partner_ids",
    "match_partner_category_ids",
    "match_journal_ids",
    "company_id",
    "unique_matching",
    "past_months_limit",
    "matching_order",
    "match_same_currency",
]


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    n43_label_match_type = fields.Selection(MATCH_TYPES, string="Readable Label Match")
    n43_label_text = fields.Char(string="Label Text")
    n43_label_case_sensitive = fields.Boolean(string="Case-sensitive Label")
    n43_label_legacy = fields.Json(string="Original Label Condition", copy=True)
    n43_migration_config = fields.Json(
        compute="_compute_n43_migration_config",
        store=True,
        copy=False,
        string="18.0 Rule Migration Snapshot",
    )

    @api.depends(
        *CONDITION_FIELDS,
        "n43_label_match_type",
        "n43_label_text",
        "n43_label_case_sensitive",
        "n43_label_legacy",
    )
    def _compute_n43_migration_config(self):
        for model in self:
            snapshot = {}
            for name in CONDITION_FIELDS:
                value = model[name]
                snapshot[name] = value.ids if model._fields[name].relational else value
            snapshot["label_rule"] = {
                "kind": model.n43_label_match_type,
                "text": model.n43_label_text,
                "case_sensitive": model.n43_label_case_sensitive,
                "legacy": model.n43_label_legacy or {},
            }
            model.n43_migration_config = snapshot

    def _n43_label_values(self, values):
        values = dict(values)
        kind = values.get("n43_label_match_type", self.n43_label_match_type)
        if kind:
            if not self.n43_label_match_type and "n43_label_legacy" not in values:
                values["n43_label_legacy"] = {
                    "match_label": values.get("match_label", self.match_label),
                    "match_label_param": values.get(
                        "match_label_param", self.match_label_param
                    ),
                }
            # Native fields are a neutral compatibility bridge, not generated rules.
            # Canonical text/options below are authoritative and survive upgrades.
            values.update(match_label="match_regex", match_label_param=".*")
        elif self.n43_label_match_type and "n43_label_match_type" in values:
            original = self.n43_label_legacy or {}
            values = {
                **{
                    key: original[key]
                    for key in ("match_label", "match_label_param")
                    if key in original
                },
                **values,
            }
        return values

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(
            [self.new({})._n43_label_values(vals) for vals in vals_list]
        )

    def write(self, vals):
        for model in self:
            super(AccountReconcileModel, model).write(model._n43_label_values(vals))
        return True

    @api.constrains("n43_label_match_type", "n43_label_text")
    def _check_n43_label(self):
        for model in self:
            if model.n43_label_match_type:
                if not model.n43_label_text:
                    raise ValidationError(self.env._("Enter the label text."))
                if model.n43_label_match_type == "regex":
                    try:
                        re.compile(model.n43_label_text)
                    except re.error as error:
                        raise ValidationError(str(error)) from error

    def _is_applicable_for(self, st_line, partner):
        self.ensure_one()
        if self.n43_label_match_type and not matches(
            self.n43_label_match_type,
            self.n43_label_text,
            st_line.payment_ref,
            self.n43_label_case_sensitive,
            self.n43_label_legacy,
        ):
            return False
        return super()._is_applicable_for(st_line, partner)

    def _n43_mapping_partners(self, st_line):
        self.ensure_one()
        partners = self.env["res.partner"]
        if self.rule_type not in ("invoice_matching", "writeoff_suggestion"):
            return partners
        note = html2plaintext(st_line.narration or "")
        for mapping in self.partner_mapping_line_ids:
            if mapping.n43_match_type:
                label_matches = matches(
                    mapping.n43_match_type,
                    mapping.n43_text,
                    st_line.payment_ref,
                    mapping.n43_case_sensitive,
                    mapping.n43_match_legacy,
                )
            else:
                label_matches = not mapping.payment_ref_regex or bool(
                    re.match(mapping.payment_ref_regex, st_line.payment_ref or "")
                )
            note_matches = not mapping.narration_regex or bool(
                re.match(mapping.narration_regex, note)
            )
            if label_matches and note_matches:
                partners |= mapping.partner_id
        return partners

    def _get_partner_from_mapping(self, st_line):
        partners = self._n43_mapping_partners(st_line)
        return partners if len(partners) == 1 else self.env["res.partner"]

    def action_n43_simplify(self):
        """Explicit opt-in; expressions not proven equivalent stay untouched."""
        for model in self:
            parsed = simple_prefix(model.match_label_param)
            if (
                parsed
                and model.match_label == "match_regex"
                and not model.n43_label_match_type
            ):
                text, _sensitive, _ascii = parsed
                model.write(
                    {
                        "n43_label_match_type": "starts_with",
                        "n43_label_text": text,
                        "n43_label_legacy": {
                            "match_label": model.match_label,
                            "match_label_param": model.match_label_param,
                            "lower": True,
                            "ignore_case": model.match_label_param.startswith("(?i)"),
                        },
                    }
                )
            for mapping in model.partner_mapping_line_ids:
                parsed = simple_prefix(mapping.payment_ref_regex)
                if parsed and not mapping.n43_match_type:
                    text, sensitive, ascii_case = parsed
                    mapping.write(
                        {
                            "n43_match_type": "starts_with",
                            "n43_text": text,
                            "n43_case_sensitive": sensitive,
                            "n43_match_legacy": {
                                "payment_ref_regex": mapping.payment_ref_regex,
                                "ascii_case": ascii_case,
                            },
                        }
                    )
        return True
