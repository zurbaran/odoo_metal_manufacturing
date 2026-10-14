# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    n43_beneficiary_enabled = fields.Boolean(string="Resolve N43 Beneficiary")
    n43_ignored_partner_ids = fields.Many2many(
        "res.partner",
        "account_journal_n43_ignored_partner_rel",
        "journal_id",
        "partner_id",
        string="Additional Account Holders",
        check_company=True,
        help="The company partner is always included. Commercial partners of these "
        "contacts are also treated as account holders.",
    )
    n43_outgoing_patterns = fields.Text(
        string="Outgoing Transfer Markers",
        default="S/ORD.TRANSF\nCASHFra\nCASHOferta\nCASHProforma",
        help="Case-insensitive literal markers, one per line. At least one must "
        "occur in the bank label. Direct debits containing CORE are excluded.",
    )
    n43_beneficiary_record = fields.Selection(
        [(f"{number:02}", f"23{number:02}") for number in range(1, 6)],
        string="Beneficiary Complementary Record",
        default="05",
        required=True,
        help="Use 2305 for the described CajaMar layout. Verify the layout before "
        "enabling another bank. Record numbering alone does not define its meaning.",
    )
    n43_allow_legacy_lines = fields.Boolean(
        string="Also Resolve Previously Imported Lines",
        help="Allow unmarked historical lines on this journal. Their beneficiary "
        "must be extracted by the configured regular expression.",
    )
    n43_legacy_beneficiary_regex = fields.Char(
        string="Historical Beneficiary Extraction",
        default=r"(?i)\bCASH(?:Fra|Oferta|Proforma)\.?\s*(?:n[.\s]*)?\S+\s+"
        r"(?P<beneficiary>.+)$",
        help="Regular expression with a named beneficiary group. Extract only "
        "the destination name, excluding holder and document reference.",
    )

    @api.constrains("n43_legacy_beneficiary_regex", "n43_allow_legacy_lines")
    def _check_n43_legacy_beneficiary_regex(self):
        for journal in self:
            pattern = journal.n43_legacy_beneficiary_regex
            if not pattern and not journal.n43_allow_legacy_lines:
                continue
            try:
                compiled = re.compile(pattern or "")
                if "beneficiary" not in compiled.groupindex:
                    raise ValueError("Missing beneficiary group")
            except (re.error, ValueError) as error:
                raise ValidationError(
                    self.env._(
                        "Provide a valid extraction regex with a named "
                        "(?P<beneficiary>...) group."
                    )
                ) from error
