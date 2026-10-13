1.  Install the addon alongside the OCA bank import and reconciliation
    addons.
2.  Open the bank journal, Advanced Settings, N43 Beneficiary.
3.  Enable Resolve N43 Beneficiary and add any additional account holder
    contacts. The company partner and commercial partners are included
    automatically.
4.  Verify the bank layout and select the beneficiary complementary
    record. The described CajaMar layout uses 2305; this is not
    universal N43 semantics.
5.  Keep `n43_partner_search = none` for the priority scenario.
6.  Configure an OCA invoice matching model per supplier, restricted to
    the bank journal, outgoing payments and the expected partner. Set
    Match Partner, add that supplier to the partner list, and keep Auto
    Reconcile disabled.
7.  Add a partner mapping matching the beneficiary name alone, for
    example `(?i).*\bTEMPLAGLASS\b.*`, `(?i).*\bVIDRIOS SALINAS\b.*` or
    `(?i).*\bVBH\b.*`. OCA uses `re.match`; a leading `.*` permits a
    substring. The VBH mapping can explicitly target VBH Iberia despite
    the bank's alias.
8.  To cover existing imports, enable Also Resolve Previously Imported
    Lines only on journals where the historical layout is known. The
    default extractor accepts CASHFra, CASHOferta and CASHProforma
    followed by a document reference and the destination name. Customize
    its named `beneficiary` group for other layouts. No reimport or
    destructive backfill is performed.

Mappings are evaluated against beneficiary-only text; put filters on
complete bank labels in the reconciliation model conditions, not the
mapping regex. Use mappings for supplier identity, never document
numbers.
