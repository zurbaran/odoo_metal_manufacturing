1. Install OCA account_reconcile_oca and l10n_es_account_statement_import_n43 for 19.0.
2. Open the bank journal, Advanced Settings, and enable Resolve N43 Beneficiary.
3. Configure additional holders to exclude (the company partner is automatic).
4. Check the layout: the verified CajaMar case uses complementary record 2305.
5. Set N43 partner search to None on the journal for the priority scenario.
6. In the Odoo 19 reconciliation models, define a mapping with a single rule
   line containing the target partner and no account. This computes mapped_partner_id.
7. Set the model's Label condition to Match Regex. Match the beneficiary's NAME,
   e.g. (?i).*TEMPLAGLASS.* or (?i).*VIDRIOS SALINAS.*.
8. Optionally restrict the journal and amount. Do not match document numbers to
   determine partner identity. Keep auto-reconciliation disabled.
9. Unmarked historical entries require explicit legacy opt-in and an extraction
   regex appropriate for the bank format.

Odoo 18's partner_mapping_line_ids, rule_type and match_nature do not exist
in the Odoo 19 model. Recreate/adjust the mappings before enabling the addon.
