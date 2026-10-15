# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import SQL


def _signed_amount_values(config):
    """Native signed bounds are a superset; exact 18.0 checks stay in the snapshot."""
    nature, kind = config.get("match_nature"), config.get("match_amount")
    minimum, maximum = (
        config.get("match_amount_min", 0),
        config.get("match_amount_max", 0),
    )
    if nature == "amount_paid":
        if kind == "lower":
            return {"match_amount": "greater", "match_amount_min": -maximum}
        if kind == "greater":
            return {"match_amount": "lower", "match_amount_max": -minimum}
        if kind == "between":
            return {
                "match_amount": "between",
                "match_amount_max": -maximum,
                "match_amount_min": -minimum,
            }
        return {"match_amount": "lower", "match_amount_max": 0}
    if nature == "amount_received":
        return {
            "match_amount": kind or "greater",
            "match_amount_min": minimum,
            "match_amount_max": maximum,
        }
    # An absolute-value interval cannot be expressed as one signed interval.
    return {"match_amount": False}


def migrate_18_mappings(env):
    """Recover original mappings after account's migration, without deleting data.

    This runs AFTER account, so it cannot fix account's regex composition error.
    The separate OpenUpgrade correction/workaround is a prerequisite.
    """
    env.cr.execute("SELECT to_regclass('account_reconcile_model_partner_mapping')")
    if not env.cr.fetchone()[0]:
        return
    env.cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'account_reconcile_model'
          AND column_name LIKE 'openupgrade_legacy_%partner_mapping_id'
        ORDER BY column_name DESC
    """)
    columns = [row[0] for row in env.cr.fetchall()]
    if not columns:
        return
    env.cr.execute(
        SQL(
            """
        SELECT target.id, to_jsonb(mapping), to_jsonb(source)
        FROM account_reconcile_model target
        JOIN account_reconcile_model_partner_mapping mapping ON %s = mapping.id
        JOIN account_reconcile_model source ON source.id = mapping.model_id
    """,
            SQL.identifier("target", columns[0]),
        )
    )
    for target_id, mapping, source in env.cr.fetchall():
        target = (
            env["account.reconcile.model"]
            .with_context(active_test=False)
            .browse(target_id)
        )
        if target.n43_source_mapping_id:
            continue
        config = source.get("n43_migration_config") or {
            key: source.get(key)
            for key in (
                "match_nature",
                "match_amount",
                "match_amount_min",
                "match_amount_max",
                "match_label",
                "match_label_param",
                "match_note",
                "match_note_param",
                "match_transaction_type",
                "match_transaction_type_param",
                "match_partner",
            )
        }
        # Relations are still native and copied by OpenUpgrade. Preserve their meaning.
        if "match_partner_ids" not in config:
            config["match_partner_ids"] = target.match_partner_ids.ids
        if "match_partner_category_ids" not in config:
            relation = "account_reconcile_model_res_partner_category_rel"
            env.cr.execute("SELECT to_regclass(%s)", [relation])
            if env.cr.fetchone()[0]:
                env.cr.execute(
                    SQL(
                        "SELECT res_partner_category_id FROM %s "
                        "WHERE account_reconcile_model_id = %s",
                        SQL.identifier(relation),
                        source["id"],
                    )
                )
                config["match_partner_category_ids"] = [
                    row[0] for row in env.cr.fetchall()
                ]
        mapping_config = mapping.get("n43_migration_config") or {
            "kind": "regex",
            "text": mapping.get("payment_ref_regex") or ".*",
            "case_sensitive": True,
            "narration_regex": mapping.get("narration_regex"),
            "label_optional": not mapping.get("payment_ref_regex"),
        }
        legacy = dict(mapping_config.get("legacy") or {})
        legacy.update(
            {
                "narration_regex": mapping_config.get("narration_regex"),
                "label_optional": mapping_config.get("label_optional", False),
                "payment_ref_regex": mapping.get("payment_ref_regex"),
                "source_mapping": mapping,
                "source_conditions": dict(config),
            }
        )
        values = {
            "n43_match_type": mapping_config["kind"],
            "n43_text": mapping_config.get("text") or ".*",
            "n43_case_sensitive": mapping_config.get("case_sensitive", False),
            "n43_match_legacy": legacy,
            "n43_source_conditions": config,
            "n43_source_mapping_id": mapping["id"],
            **_signed_amount_values(config),
        }
        if not config.get("match_partner"):
            values["match_partner_ids"] = [(5, 0, 0)]
        if source.get("n43_migration_config"):
            # Restore the mapping's actual prior state, not a guessed active=True.
            values["active"] = bool(config.get("active"))
        label_rule = config.get("label_rule") or {}
        if label_rule.get("kind"):
            values.update(
                n43_label_match_type=label_rule["kind"],
                n43_label_text=label_rule.get("text"),
                n43_label_case_sensitive=label_rule.get("case_sensitive", False),
                n43_label_legacy=label_rule.get("legacy") or {},
            )
        # Never write trigger: preserve the decision made by account's migration.
        target.write(values)


def preserve_19_mappings(env):
    """Retain the first 19.0 port's Python search + IGNORECASE semantics."""
    models = (
        env["account.reconcile.model"]
        .with_context(active_test=False)
        .search(
            [
                ("mapped_partner_id", "!=", False),
                ("n43_match_type", "=", False),
                ("match_label", "in", ["contains", "match_regex"]),
            ]
        )
    )
    for model in models:
        if not model.match_label_param:
            continue
        legacy = {
            "match_label": model.match_label,
            "match_label_param": model.match_label_param,
        }
        if model.match_label == "match_regex":
            legacy.update(search=True, ignore_case=True)
            kind = "regex"
        else:
            kind = "contains"
            legacy["casefold"] = True
        model.write(
            {
                "n43_match_type": kind,
                "n43_text": model.match_label_param,
                "n43_match_legacy": legacy,
            }
        )


def post_init_hook(env):
    migrate_18_mappings(env)
