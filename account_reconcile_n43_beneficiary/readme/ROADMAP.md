Unknown beneficiaries and conflicting applicable models return an empty
partner. Configure supplier models with Match Partner enabled so they
cannot suggest another supplier merely because a reference number
matches. Generic existing models that permit an empty partner retain
their upstream behavior and must be reviewed separately. This addon does
not impose a global safety policy on OCA.

Conflicts between models are rejected; within one model, the first
matching partner mapping follows OCA semantics. Keep mappings specific
and non-overlapping.

Structured concepts are retained for new imports. Historical lines
require explicit journal opt-in and a suitable extraction regex. Other
bank formats on that opted-in journal can also match this regex, so
verify the layout first.

The current fix remains limited to beneficiary resolution. Correct
partner identity does not by itself guarantee a suggestion: OCA's
account, date, currency, reference, residual and model conditions still
apply.
