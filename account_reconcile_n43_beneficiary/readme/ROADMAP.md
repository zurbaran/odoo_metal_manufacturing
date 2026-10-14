This addon resolves only partner identity, not matching against an
outstanding invoice or payment. Reconciliation models and matching criteria
must be configured separately using Odoo 19 / OCA.

Odoo 19 partner mapping models are based on mapped_partner_id and match_label,
not the Odoo 18 mapping-line structure. Conflicting models leave the partner
blank. Validate bank-specific N43 complementary records before enabling.
