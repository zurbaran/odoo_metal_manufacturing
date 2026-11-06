import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _auto_assign_journal(self):
        for move in self:
            if not move.company_id or not move.is_invoice(include_receipts=True):
                continue
            journal = move.journal_id
            if (
                journal
                and journal.type in move._get_valid_journal_types()
                and journal.filtered_domain(
                    self.env["account.journal"]._check_company_domain(move.company_id)
                )
            ):
                continue
            # Use the native selector, including currency and branch semantics,
            # to repair the journal left over after changing company in a form.
            move.journal_id = move._search_default_journal()
            _logger.info(
                "Selected journal %s for company %s and invoice type %s",
                move.journal_id.id,
                move.company_id.id,
                move.move_type,
            )

    @api.onchange("company_id", "move_type")
    def _onchange_company_or_type(self):
        self._auto_assign_journal()
