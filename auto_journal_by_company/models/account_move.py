import logging  # Módulo estándar de Python para gestión de logs

from odoo import api, models  # Importación de la API de Odoo para modelos y decoradores

# Instancia de logger específica para este módulo, usando el nombre completo
# del módulo como identificador.
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
          - Si `journal_id` ya está establecido, no se modifica (se respeta
            una posible selección manual u otro mecanismo previo).
          - Se registran logs en nivel DEBUG, INFO y WARNING para facilitar
            el diagnóstico de la selección automática.
        """
        # El onchange se aplica sobre todos los registros en el recordset "self"
        for move in self:
            # Log de depuración: muestra los valores relevantes antes de la lógica
            _logger.debug(
                (
                    "[auto_journal_by_company] ONCHANGE triggered: "
                    "company_id=%s, move_type=%s, journal_id=%s"
                ),
                move.company_id.id,
                move.move_type,
                move.journal_id.id if move.journal_id else None,
            )

            # Si el diario ya está definido, no hacemos nada más para este registro
            if move.journal_id:
                _logger.debug(
                    (
                        "[auto_journal_by_company] journal_id already set "
                        "(%s), skipping auto-selection"
                    ),
                    move.journal_id.id,
                )
                # `continue` pasa al siguiente `move` del recordset
                continue

            # Determinación del tipo de diario en función del tipo de movimiento
            journal_type = False
            if move.move_type == "out_invoice":
                # Facturas de cliente usan diarios de tipo 'sale'
                journal_type = "sale"
            elif move.move_type == "in_invoice":
                # Facturas de proveedor usan diarios de tipo 'purchase'
                journal_type = "purchase"

            # Solo si se ha determinado un tipo de diario y hay compañía definida
            if journal_type and move.company_id:
                # Búsqueda del diario adecuado para esa empresa y tipo
                journal = self.env["account.journal"].search(
                    [
                        ("type", "=", journal_type),
                        ("company_id", "=", move.company_id.id),
                        ("active", "=", True),
                    ],
                    limit=1,  # Solo el primer diario encontrado
                )
                if journal:
                    # Asignación del diario encontrado al movimiento
                    move.journal_id = journal
                    _logger.info(
                        (
                            "[auto_journal_by_company] ONCHANGE: "
                            "journal_id set to %s (%s)"
                        ),
                        journal.id,
                        journal.name,
                    )
                else:
                    # Aviso si no se encuentra ningún diario compatible
                    _logger.warning(
                        (
                            "[auto_journal_by_company] ONCHANGE: "
                            "No journal found for type '%s' and company %s"
                        ),
                        journal_type,
                        move.company_id.name,
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescritura del método `create` para aplicar la misma lógica de
        asignación automática de diario durante la creación de movimientos.

        Parámetros:
          - vals_list: lista de diccionarios con los valores de los campos
            para cada registro a crear.

        Comportamiento:
          - Se llama primero a `super().create(vals_list)` para que Odoo
            cree los registros.
          - Para cada movimiento creado:
              * Si `journal_id` NO se ha especificado en vals
              * Y existen `company_id` y `move_type` en vals
                => se intenta localizar un diario apropiado:
                    - `out_invoice`  -> `sale`
                    - `in_invoice`   -> `purchase`
              * Si se encuentra un diario, se asigna al movimiento.
          - Si `journal_id` está definido o faltan datos, se deja tal cual.

        Notas:
          - Se usa `zip(moves, vals_list, strict=False)` para iterar en
            paralelo sobre los registros creados y sus valores originales.
          - Se registran logs de tipo INFO y WARNING para trazar el proceso.
        """
        # Creación real de los movimientos mediante la implementación nativa
        moves = super().create(vals_list)

        # Recorremos simultáneamente cada movimiento creado y su diccionario de valores
        for move, vals in zip(moves, vals_list, strict=False):
            # Condición principal: solo si NO se indicó `journal_id`
            # y SI hay `company_id` y `move_type` en los valores de creación.
            if (
                not vals.get("journal_id")
                and vals.get("company_id")
                and vals.get("move_type")
            ):
                # Mapeo desde move_type al tipo de diario correspondiente
                journal_type = {
                    "out_invoice": "sale",
                    "in_invoice": "purchase",
                }.get(vals["move_type"])

                if journal_type:
                    # Búsqueda del diario que encaja con tipo y compañía
                    journal = self.env["account.journal"].search(
                        [
                            ("type", "=", journal_type),
                            ("company_id", "=", vals["company_id"]),
                            ("active", "=", True),
                        ],
                        limit=1,
                    )
                    if journal:
                        # Asignación del diario al movimiento recién creado
                        move.journal_id = journal
                        message = (
                            "[auto_journal_by_company] CREATE: "
                            "Asignado journal_id=%s (%s) para company_id=%s"
                        )
                        _logger.info(
                            message,
                            journal.id,
                            journal.name,
                            vals["company_id"],
                        )
                    else:
                        # No se encontró diario compatible: se lanza un warning
                        _logger.warning(
                            (
                                "[auto_journal_by_company] CREATE: "
                                "No se encontró diario para tipo '%s' y "
                                "empresa %s"
                            ),
                            journal_type,
                            vals["company_id"],
                        )
            else:
                # Caso en el que ya existe un diario en vals o faltan datos mínimos:
                # se deja la lógica por defecto y solo se registra en DEBUG.
                _logger.debug(
                    (
                        "[auto_journal_by_company] CREATE: journal_id ya "
                        "definido o datos insuficientes para move_type=%s"
                    ),
                    vals.get("move_type"),
                )

        # Devolvemos el recordset creado, como en el comportamiento estándar
        return moves
