Resolve the beneficiary of outgoing N43 transfers when OCA would
otherwise select the account holder from `partner_name` or `partner_id`.

The addon returns a partner only. It neither implements reconciliation
nor creates invoices, payments or entries. Original bank fields are
untouched.


Readable label and partner criteria support Starts with, Contains, Ends with,
Exactly equals and advanced Python regular expressions. Plain text is stored
with its options, rather than as a generated expression. Existing native
conditions and mappings remain available. Ambiguous applicable mappings do not
choose a partner by sequence.
