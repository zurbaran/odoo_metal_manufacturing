Open an un-reconciled imported outgoing transfer in the OCA
reconciliation UI. For the enabled journal, an account-holder result is
replaced with the unique beneficiary mapping that satisfies the original
model's applicability filters. Then OCA searches candidate journal items
using that partner and its own rules.

Incoming transfers, CORE direct debits, unrecognized transfer labels,
disabled journals, already reconciled lines and explicitly selected
third parties keep the upstream behavior. The import-time
`skip_retrieve_partner` context is respected. Lookup does not change the
persisted partner or original bank text.

With `n43_partner_search = all`, an imported account-holder partner is
corrected when resolving at reconciliation time. Other imported partners
remain trusted, so `all` is not recommended when bank heuristics can
select unrelated parties.
