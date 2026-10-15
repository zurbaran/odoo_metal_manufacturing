# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _parse_single_file_n43(self, n43):
        result = super()._parse_single_file_n43(n43)
        for statement in result[2]:
            for transaction in statement["transactions"]:
                transaction["n43_imported"] = True
                transaction["n43_complementary_concepts"] = transaction["n43_line"][
                    "conceptos"
                ]
        return result

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        """Resolve before creation: N43 importer sets skip_retrieve_partner.

        OCA 19 deliberately skips partner retrieval on statement-line create,
        so this complement must be applied at the import wizard stage.
        """
        result = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        if not journal.n43_beneficiary_enabled:
            return result
        StatementLine = self.env["account.bank.statement.line"]
        for statement in result:
            for transaction in statement["transactions"]:
                if not transaction.get("n43_imported"):
                    continue
                candidate = StatementLine.new(
                    {
                        **transaction,
                        "journal_id": journal.id,
                        "company_id": journal.company_id.id,
                    }
                )
                if candidate._n43_is_outgoing_transfer():
                    partner = candidate._n43_resolved_partner()
                    transaction["partner_id"] = partner.id or False
        return result
