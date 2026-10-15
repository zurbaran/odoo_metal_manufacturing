# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..utils.text_matching import MATCH_TYPES


class AccountReconcileModelPartnerMapping(models.Model):
    _inherit = "account.reconcile.model.partner.mapping"

    n43_match_type = fields.Selection(MATCH_TYPES, string="Label Match Type")
    n43_text = fields.Char(string="Text")
    n43_case_sensitive = fields.Boolean(string="Case-sensitive")
    n43_match_legacy = fields.Json(string="Original Mapping", copy=True)
    n43_migration_config = fields.Json(
        compute="_compute_n43_migration_config",
        store=True,
        copy=False,
        string="18.0 Mapping Migration Snapshot",
    )

    @api.depends(
        "payment_ref_regex",
        "narration_regex",
        "n43_match_type",
        "n43_text",
        "n43_case_sensitive",
        "n43_match_legacy",
    )
    def _compute_n43_migration_config(self):
        for mapping in self:
            mapping.n43_migration_config = {
                "kind": mapping.n43_match_type or "regex",
                "text": mapping.n43_text
                if mapping.n43_match_type
                else mapping.payment_ref_regex,
                "case_sensitive": mapping.n43_case_sensitive,
                "narration_regex": mapping.narration_regex,
                "original": mapping.n43_match_legacy or {},
                "legacy": mapping.n43_match_legacy or {},
                "label_optional": not (
                    mapping.n43_match_type or mapping.payment_ref_regex
                ),
            }

    def _n43_mapping_values(self, vals):
        vals = dict(vals)
        kind = vals.get("n43_match_type", self.n43_match_type)
        if kind:
            if not self.n43_match_type and "n43_match_legacy" not in vals:
                vals["n43_match_legacy"] = {
                    "payment_ref_regex": vals.get(
                        "payment_ref_regex", self.payment_ref_regex
                    ),
                }
            vals["payment_ref_regex"] = ".*"
        elif self.n43_match_type and "n43_match_type" in vals:
            original = self.n43_match_legacy or {}
            if "payment_ref_regex" in original:
                vals = {"payment_ref_regex": original["payment_ref_regex"], **vals}
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(
            [self.new({})._n43_mapping_values(vals) for vals in vals_list]
        )

    def write(self, vals):
        for mapping in self:
            super(AccountReconcileModelPartnerMapping, mapping).write(
                mapping._n43_mapping_values(vals)
            )
        return True

    @api.constrains("n43_match_type", "n43_text")
    def _check_n43_text(self):
        for mapping in self:
            if mapping.n43_match_type:
                if not mapping.n43_text:
                    raise ValidationError(self.env._("Enter the mapping text."))
                if mapping.n43_match_type == "regex":
                    try:
                        re.compile(mapping.n43_text)
                    except re.error as error:
                        raise ValidationError(str(error)) from error
