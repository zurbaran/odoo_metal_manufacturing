N43 Beneficiary Partner Resolution (Odoo 19)
============================================

Resolve outgoing N43 beneficiary names using Odoo 19 partner-mapping
reconciliation models. Original N43 concept records are preserved.

Dependencies: account_reconcile_oca and l10n_es_account_statement_import_n43.

Enable beneficiary resolution in the bank journal and choose the verified
complementary record (CajaMar example: 2305). Use a reconciliation model
with one partner-only rule line (mapped_partner_id) and a beneficiary-name
regex (match_label / match_label_param). Restrict journal and amount as needed.

Odoo 18 partner_mapping_line_ids, rule_type and match_nature are no longer
available in Odoo 19. Migrate reconciliation mapping DATA separately.

Ambiguous matches remain unassigned. This addon never auto-reconciles.

See readme/CONFIGURE.md and readme/USAGE.md for instructions.

https://github.com/zurbaran/odoo_metal_manufacturing/tree/19.0/account_reconcile_n43_beneficiary
