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
