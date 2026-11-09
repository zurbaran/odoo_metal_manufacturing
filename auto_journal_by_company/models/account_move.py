import logging

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _auto_assign_journal(self):
        for move in self:
            _logger.debug(
                "[auto_journal_by_company] AUTO: evaluating move %s "
                "(company_id=%s, move_type=%s, journal_id=%s)",
                move.id or "(new)",
                move.company_id.id,
                move.move_type,
                move.journal_id.id,
            )
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
                _logger.debug(
                    "[auto_journal_by_company] AUTO: keeping existing "
                    "journal_id=%s for move %s",
                    journal.id,
                    move.id or "(new)",
                )
                continue
            # Use the native selector, including currency and branch semantics,
            # to repair the journal left over after changing company in a form.
            try:
                journal = move._search_default_journal()
            except UserError:
                # Preserve the 18.0 helper's non-blocking behavior while a
                # company is being configured. Native create/posting still
                # enforce a valid journal before saving an invoice.
                _logger.warning(
                    "[auto_journal_by_company] AUTO: no journal found for "
                    "type '%s' and company %s (move %s)",
                    move.move_type,
                    move.company_id.name,
                    move.id or "(new)",
                )
                continue
            move.journal_id = journal
            _logger.info(
                "[auto_journal_by_company] AUTO: selected journal %s "
                "for company %s and invoice type %s",
                move.journal_id.id,
                move.company_id.id,
                move.move_type,
            )

    @api.onchange("company_id", "move_type")
    def _onchange_company_or_type(self):
        self._auto_assign_journal()
