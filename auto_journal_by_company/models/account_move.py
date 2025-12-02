import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """
    Extensión del modelo `account.move` para asignar automáticamente el diario
    (journal) en función de:
      - La compañía (`company_id`)
      - El tipo de movimiento (`move_type`: factura de cliente o proveedor)

    Comportamiento principal:
      - En el onchange de `company_id` o `move_type` se intenta asignar un
        diario por defecto coherente con la empresa y el tipo de factura.
      - En la creación (`create`) de movimientos contables se aplica la misma
        lógica, siempre que no se haya indicado manualmente un diario.
    """

    _inherit = "account.move"

    # -------------------------------------------------------------------------
    # Lógica común
    # -------------------------------------------------------------------------
    def _auto_assign_journal(self):
        """
        Asigna automáticamente un diario adecuado en función de:

          - company_id del movimiento
          - move_type (out_invoice / in_invoice)

        Reglas:
          - Si ya hay journal_id y pertenece a la misma compañía, no se toca.
          - Solo se actúa cuando:
              * existe company_id
              * move_type es soportado (out_invoice / in_invoice)
          - Si no se encuentra diario compatible, se deja tal cual y se hace
            un log WARNING.
        """
        for move in self:
            _logger.debug(
                "[auto_journal_by_company] AUTO: evaluating move %s "
                "(company_id=%s, move_type=%s, journal_id=%s)",
                move.id or "(new)",
                move.company_id.id if move.company_id else None,
                move.move_type,
                move.journal_id.id if move.journal_id else None,
            )

            # Si ya hay diario y es de la misma compañía, no hacemos nada
            if move.journal_id and move.journal_id.company_id == move.company_id:
                _logger.debug(
                    "[auto_journal_by_company] AUTO: keeping existing "
                    "journal_id=%s for move %s",
                    move.journal_id.id,
                    move.id or "(new)",
                )
                continue

            # Determinar tipo de diario según el tipo de movimiento
            journal_type = {
                "out_invoice": "sale",
                "in_invoice": "purchase",
                # Si quisieras incluir abonos en el futuro:
                # "out_refund": "sale",
                # "in_refund": "purchase",
            }.get(move.move_type)

            if not journal_type or not move.company_id:
                _logger.debug(
                    "[auto_journal_by_company] AUTO: skipping move %s "
                    "(journal_type=%s, company_id=%s)",
                    move.id or "(new)",
                    journal_type,
                    move.company_id.id if move.company_id else None,
                )
                continue

            # Buscar diario adecuado para esa empresa y tipo
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
                    "[auto_journal_by_company] AUTO: journal_id set to %s (%s) "
                    "for move %s (company_id=%s, move_type=%s)",
                    journal.id,
                    journal.name,
                    move.id or "(new)",
                    move.company_id.id,
                    move.move_type,
                )
            else:
                _logger.warning(
                    "[auto_journal_by_company] AUTO: no journal found for "
                    "type '%s' and company %s (move %s)",
                    journal_type,
                    move.company_id.name,
                    move.id or "(new)",
                )

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------
    @api.onchange("company_id", "move_type")
    def _onchange_company_or_type(self):
        """
        Onchange de `company_id` y `move_type`.

        Objetivo:
          - Cuando se cambie la empresa o el tipo de movimiento, se busca
            automáticamente un diario (journal) apropiado:
              * Para `out_invoice` -> diario de tipo `sale`
              * Para `in_invoice`  -> diario de tipo `purchase`

        Detalles:
          - Si `journal_id` ya está establecido y pertenece a la misma empresa,
            no se modifica (se respeta la selección manual o por defecto).
          - Se apoyan los logs definidos en `_auto_assign_journal`.
        """
        self._auto_assign_journal()

    # -------------------------------------------------------------------------
    # Create
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescritura del método `create` para aplicar la lógica de
        asignación automática de diario durante la creación de movimientos.

        Comportamiento:
          - Se llama primero a `super().create(vals_list)` para que Odoo
            cree los registros.
          - Para cada movimiento creado:
              * Si `journal_id` SE HA especificado en vals -> se respeta.
              * Si no se ha especificado, se llama a `_auto_assign_journal`
                para que el diario se asigne en función de company_id y
                move_type finales del movimiento.
          - No se sobrescribe un diario ya correcto de la misma empresa.
        """
        moves = super().create(vals_list)

        auto_moves = self.browse()
        manual_moves = self.browse()

        # Clasificamos movimientos según si venían con journal_id explícito
        for move, vals in zip(moves, vals_list):
            if vals.get("journal_id"):
                manual_moves |= move
            else:
                auto_moves |= move

        if manual_moves:
            _logger.debug(
                "[auto_journal_by_company] CREATE: %s moves with manual "
                "journal_id, skipping auto-assignment",
                len(manual_moves),
            )

        if auto_moves:
            _logger.debug(
                "[auto_journal_by_company] CREATE: %s moves without "
                "journal_id in vals, running auto-assignment",
                len(auto_moves),
            )
            auto_moves._auto_assign_journal()

        return moves
