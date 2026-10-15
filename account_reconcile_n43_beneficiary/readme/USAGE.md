Import an N43 file. For enabled bank journals, the beneficiary complementary
record is preserved independently and matched to a unique Odoo 19 mapping
model. A valid non-holder partner is never replaced.

Resolution happens before statement-line creation because the OCA importer
sets skip_retrieve_partner in its creation context. Re-running partner
retrieval on existing lines is also supported, with the journal's optional
legacy extraction configuration for unmarked historical data.

Unrecognized or conflicting beneficiaries are left unassigned for manual
review. No invoice, payment or bank reconciliation is created by this addon.


See the [migration guide](https://github.com/zurbaran/odoo_metal_manufacturing/blob/19.0/account_reconcile_n43_beneficiary/MIGRATION_ES.md) and [validation report](https://github.com/zurbaran/odoo_metal_manufacturing/blob/19.0/account_reconcile_n43_beneficiary/VALIDATION.md) before rollout.
