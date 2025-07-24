import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("company_id", "move_type")
    def _onchange_company_or_type(self):
        for move in self:
            _logger.debug(
                "[auto_journal_by_company] ONCHANGE triggered: company_id=%s, move_type=%s, journal_id=%s",
                move.company_id.id,
                move.move_type,
                move.journal_id.id if move.journal_id else None,
            )

            if move.journal_id:
                _logger.debug(
                    "[auto_journal_by_company] journal_id already set (%s), skipping auto-selection",
                    move.journal_id.id,
                )
                continue

            journal_type = False
            if move.move_type == "out_invoice":
                journal_type = "sale"
            elif move.move_type == "in_invoice":
                journal_type = "purchase"

            if journal_type and move.company_id:
                journal = self.env["account.journal"].search(
                    [
                        ("type", "=", journal_type),
                        ("company_id", "=", move.company_id.id),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
                if journal:
                    move.journal_id = journal
                    _logger.info(
                        "[auto_journal_by_company] ONCHANGE: journal_id set to %s (%s)",
                        journal.id,
                        journal.name,
                    )
                else:
                    _logger.warning(
                        "[auto_journal_by_company] ONCHANGE: No journal found for type '%s' and company %s",
                        journal_type,
                        move.company_id.name,
                    )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move, vals in zip(moves, vals_list, strict=False):
            if (
                not vals.get("journal_id")
                and vals.get("company_id")
                and vals.get("move_type")
            ):
                journal_type = {"out_invoice": "sale", "in_invoice": "purchase"}.get(
                    vals["move_type"]
                )
                if journal_type:
                    journal = self.env["account.journal"].search(
                        [
                            ("type", "=", journal_type),
                            ("company_id", "=", vals["company_id"]),
                            ("active", "=", True),
                        ],
                        limit=1,
                    )
                    if journal:
                        move.journal_id = journal
                        _logger.info(
                            "[auto_journal_by_company] CREATE: Asignado journal_id=%s (%s) para company_id=%s",
                            journal.id,
                            journal.name,
                            vals["company_id"],
                        )
                    else:
                        _logger.warning(
                            "[auto_journal_by_company] CREATE: No se encontró diario para tipo '%s' y empresa %s",
                            journal_type,
                            vals["company_id"],
                        )
            else:
                _logger.debug(
                    "[auto_journal_by_company] CREATE: journal_id ya definido o datos insuficientes para move_type=%s",
                    vals.get("move_type"),
                )

        return moves
