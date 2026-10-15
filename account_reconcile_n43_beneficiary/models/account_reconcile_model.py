# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

import psycopg2

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL, html2plaintext

from ..utils.text_matching import MATCH_TYPES, matches, simple_prefix


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    n43_label_match_type = fields.Selection(MATCH_TYPES, string="Readable Label Match")
    n43_label_text = fields.Char(string="Label Text")
    n43_label_case_sensitive = fields.Boolean(string="Case-sensitive Label")
    n43_label_legacy = fields.Json(string="Original Label Condition", copy=True)
    n43_match_type = fields.Selection(MATCH_TYPES, string="Partner Label Match Type")
    n43_text = fields.Char(string="Partner Identification Text")
    n43_case_sensitive = fields.Boolean(string="Case-sensitive Partner Match")
    n43_match_legacy = fields.Json(string="Original Partner Mapping", copy=True)
    n43_source_conditions = fields.Json(string="Preserved 18.0 Conditions", copy=True)
    n43_source_mapping_id = fields.Integer(string="Source 18.0 Mapping ID", copy=False)
    # Same column as 18.0: do not recompute it using the reduced 19.0 schema.
    n43_migration_config = fields.Json(
        string="18.0 Rule Migration Snapshot", copy=False
    )

    def _n43_bridge_values(self, vals):
        vals = dict(vals)
        label = vals.get("n43_label_match_type", self.n43_label_match_type)
        mapping = vals.get("n43_match_type", self.n43_match_type)
        if label or mapping:
            archive_key = "n43_match_legacy" if mapping else "n43_label_legacy"
            was_managed = self.n43_label_match_type or self.n43_match_type
            if not was_managed and archive_key not in vals:
                vals[archive_key] = {
                    "match_label": vals.get("match_label", self.match_label),
                    "match_label_param": vals.get(
                        "match_label_param", self.match_label_param
                    ),
                }
            vals.update(match_label="match_regex", match_label_param=".*")
        elif self.n43_label_match_type or self.n43_match_type:
            original = self.n43_match_legacy or self.n43_label_legacy or {}
            vals = {
                **{
                    key: original[key]
                    for key in ("match_label", "match_label_param")
                    if key in original
                },
                **vals,
            }
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(
            [self.new({})._n43_bridge_values(vals) for vals in vals_list]
        )

    def write(self, vals):
        for model in self:
            values = dict(vals)
            if model.n43_source_conditions and "n43_source_conditions" not in values:
                config = dict(model.n43_source_conditions)
                if {
                    "match_amount",
                    "match_amount_min",
                    "match_amount_max",
                }.intersection(values):
                    # An explicit edit now uses the native signed 19.0 condition.
                    for key in (
                        "match_amount",
                        "match_amount_min",
                        "match_amount_max",
                        "match_nature",
                    ):
                        config.pop(key, None)
                if "match_partner_ids" in values:
                    config.pop("match_partner_ids", None)
                if config != model.n43_source_conditions:
                    values["n43_source_conditions"] = config
            super(AccountReconcileModel, model).write(model._n43_bridge_values(values))
        return True

    @api.constrains(
        "n43_label_match_type",
        "n43_label_text",
        "n43_match_type",
        "n43_text",
        "line_ids",
    )
    def _check_n43_text(self):
        for model in self:
            for kind, text in [
                (model.n43_label_match_type, model.n43_label_text),
                (model.n43_match_type, model.n43_text),
            ]:
                if kind:
                    if not text:
                        raise ValidationError(self.env._("Enter the matching text."))
                    if kind == "regex":
                        try:
                            re.compile(text)
                        except re.error as error:
                            raise ValidationError(str(error)) from error
            if model.n43_match_type and not model.mapped_partner_id:
                raise ValidationError(
                    self.env._(
                        "A partner mapping needs exactly one counterpart line with "
                        "a partner and no account."
                    )
                )

    @api.constrains("match_label", "match_label_param")
    def _check_n43_native_pg_regex(self):
        """Native OCA SQL regexes must also compile in PostgreSQL.

        Managed Python expressions never enter this SQL path: the native field
        is deliberately neutral. No syntax is silently translated.
        """
        for model in self:
            if model.match_label == "match_regex" and not (
                model.n43_label_match_type or model.n43_match_type
            ):
                try:
                    with self.env.cr.savepoint():
                        self.env.cr.execute(
                            "SELECT '' ~* %s", [model.match_label_param]
                        )
                except psycopg2.Error as error:
                    raise ValidationError(
                        self.env._(
                            "This native expression is not valid in PostgreSQL. "
                            "Use the advanced Python matching field instead."
                        )
                    ) from error

    def _n43_native_label_matches(self, value):
        self.ensure_one()
        if not self.match_label:
            return True
        pattern = self.match_label_param or ""
        if self.match_label == "match_regex":
            try:
                with self.env.cr.savepoint():
                    self.env.cr.execute("SELECT %s ~* %s", [value or "", pattern])
                    return bool(self.env.cr.fetchone()[0])
            except psycopg2.Error as error:
                raise ValidationError(
                    self.env._(
                        "This native expression cannot run in PostgreSQL. "
                        "Configure an advanced Python rule instead."
                    )
                ) from error
        else:
            self.env.cr.execute(
                "SELECT %s ILIKE '%%' || %s || '%%'", [value or "", pattern]
            )
        result = self.env.cr.fetchone()[0]
        return not result if self.match_label == "not_contains" else bool(result)

    def _n43_mapping_matches(self, label, note=""):
        self.ensure_one()
        if not self.n43_match_type:
            return self._n43_native_label_matches(label)
        legacy = self.n43_match_legacy or {}
        label_matches = legacy.get("label_optional") or matches(
            self.n43_match_type,
            self.n43_text,
            label,
            self.n43_case_sensitive,
            legacy,
        )
        note_regex = legacy.get("narration_regex")
        note_matches = not note_regex or bool(
            re.match(note_regex, html2plaintext(note or ""))
        )
        return bool(label_matches and note_matches)

    def _n43_conditions_apply(self, st_line, partner):
        self.ensure_one()
        if self.company_id != st_line.company_id:
            return False
        if self.match_journal_ids and st_line.journal_id not in self.match_journal_ids:
            return False
        if self.match_partner_ids and partner not in self.match_partner_ids:
            return False
        if self.match_amount == "lower" and st_line.amount > self.match_amount_max:
            return False
        if self.match_amount == "greater" and st_line.amount < self.match_amount_min:
            return False
        if self.match_amount == "between" and not (
            self.match_amount_max <= st_line.amount <= self.match_amount_min
        ):
            return False
        if self.n43_label_match_type and not matches(
            self.n43_label_match_type,
            self.n43_label_text,
            st_line.payment_ref,
            self.n43_label_case_sensitive,
            self.n43_label_legacy,
        ):
            return False
        return self._n43_source_conditions_apply(st_line, partner)

    def _n43_source_conditions_apply(self, line, partner):
        """Replay preserved OCA 18 conditions without compiling them as SQL."""
        config = self.n43_source_conditions or {}
        if not config:
            return True
        nature = config.get("match_nature")
        if (nature == "amount_paid" and line.amount > 0) or (
            nature == "amount_received" and line.amount < 0
        ):
            return False
        amount = abs(line.amount)
        kind = config.get("match_amount")
        lower, upper = (
            config.get("match_amount_min", 0),
            config.get("match_amount_max", 0),
        )
        if (
            (kind == "lower" and amount >= upper)
            or (kind == "greater" and amount <= lower)
            or (kind == "between" and not lower <= amount <= upper)
        ):
            return False
        if config.get("match_partner"):
            if not partner:
                return False
            allowed = config.get("match_partner_ids")
            if allowed and partner.id not in allowed:
                return False
            categories = config.get("match_partner_category_ids")
            if categories and not set(partner.category_id.ids).intersection(categories):
                return False
        rule = config.get("label_rule") or {}
        if self.n43_label_match_type:
            # The visible, explicitly editable criterion replaces the old one.
            pass
        elif rule.get("kind"):
            if not matches(
                rule["kind"],
                rule.get("text"),
                line.payment_ref,
                rule.get("case_sensitive", False),
                rule.get("legacy"),
            ):
                return False
        elif not self._n43_old_condition(
            config.get("match_label"), config.get("match_label_param"), line.payment_ref
        ):
            return False
        transaction = (
            line["transaction_type"] if "transaction_type" in line._fields else ""
        )
        return self._n43_old_condition(
            config.get("match_note"), config.get("match_note_param"), line.narration
        ) and self._n43_old_condition(
            config.get("match_transaction_type"),
            config.get("match_transaction_type_param"),
            transaction,
        )

    @staticmethod
    def _n43_old_condition(kind, pattern, value):
        """Mirror 18.0 _is_applicable_for, including its lowercasing convention."""
        pattern, value = (pattern or "").lower(), (value or "").lower()
        if kind == "contains":
            return pattern in value
        if kind == "not_contains":
            return pattern not in value
        if kind == "match_regex":
            return bool(re.match(pattern, value))
        return True

    def _get_rules_query(self, bank_statement_lines, trigger="auto_reconcile"):
        query = super()._get_rules_query(bank_statement_lines, trigger=trigger)
        managed = self.search(
            [
                "|",
                ("n43_label_match_type", "!=", False),
                ("n43_source_conditions", "!=", False),
            ]
        )
        if managed:
            pairs = tuple(
                (model.id, line.id)
                for model in managed
                for line in bank_statement_lines
                if model._n43_conditions_apply(line, line.partner_id)
            )
            unmanaged = SQL(
                "%s NOT IN %s", SQL.identifier(self._table, "id"), tuple(managed.ids)
            )
            if pairs:
                query.add_where(
                    SQL(
                        "(%s OR (%s, %s) IN %s)",
                        unmanaged,
                        SQL.identifier(self._table, "id"),
                        SQL.identifier(bank_statement_lines._table, "id"),
                        pairs,
                    )
                )
            else:
                query.add_where(unmanaged)
        return query

    def action_n43_simplify(self):
        for model in self:
            if model.n43_match_type:
                parsed = (
                    simple_prefix(model.n43_text)
                    if model.n43_match_type == "regex"
                    else None
                )
            elif model.mapped_partner_id and model.match_label == "match_regex":
                parsed = simple_prefix(model.match_label_param)
            else:
                parsed = None
            if parsed:
                text, sensitive, ascii_case = parsed
                legacy = dict(model.n43_match_legacy or {})
                if not model.n43_match_type:
                    legacy.update(
                        match_label=model.match_label,
                        match_label_param=model.match_label_param,
                    )
                if legacy.get("search") or legacy.get("ignore_case"):
                    # Already-ported 19.0 native regexes used IGNORECASE search.
                    # Anchored prefix syntax remains anchored, with Unicode casing.
                    sensitive, ascii_case = False, False
                legacy.update(ascii_case=ascii_case, search=False, ignore_case=False)
                model.write(
                    {
                        "n43_match_type": "starts_with",
                        "n43_text": text,
                        "n43_case_sensitive": sensitive,
                        "n43_match_legacy": legacy,
                    }
                )
        return True
