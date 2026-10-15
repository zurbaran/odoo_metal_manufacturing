1. Install OCA **account_reconcile_oca** and the N43 importer for 19.0. Enable
   **Resolve N43 Beneficiary** in the bank journal and keep N43 partner search
   at **None** for the priority scenario. Add only actual additional holders.
2. Check an original bank file. Complementary record `2305` (selection `05`) is
   the expected CajaMar layout and still needs validation against the real file.
3. In the native reconciliation model, create EXACTLY ONE counterpart line with
   the target **Partner** and NO account. Odoo computes `mapped_partner_id`.
   Keep the trigger **Manual** unless automation has separately been authorized.
4. Under **Readable Matching > Partner Identification**, select a match type,
   enter literal text and choose case sensitivity. Examples:

   | Match type | Text | Case-sensitive | Counterpart partner |
   | --- | --- | --- | --- |
   | Starts with | COREMUTUA | No | Mutua Madrileña |
   | Contains | TEMPLAGLASS | No | Templaglass S.L. |
   | Contains | VIDRIOS SALINAS | No | Vidrios Salinas, S.L. |
   | Contains | VBH | No | VBH Iberia, S.L. |

5. Use **Bank Label Condition** for an additional condition on the COMPLETE bank
   label, independently of identifying the beneficiary. Restrict journal,
   partners and signed amount through the native fields when appropriate.
6. N43 supplier matching uses the extracted beneficiary name, excluding the
   holder and invoice reference. Ordinary CORE matching uses the full label.
   Distinct applicable partners are ambiguous: no partner is chosen by sequence.
7. Plain text is literal, including `%`, `_`, brackets and dots. Starts with is
   anchored; Contains is not; Exactly equals does not accept extra characters.
   Advanced **Python** regex uses `re.match`, with its original flags. Python
   expressions are not sent to PostgreSQL. Native advanced conditions remain
   available and are checked in Python AND PostgreSQL, because native OCA SQL
   executes them with `~*`. Their engine and search semantics differ.
8. On upgrading the first 19.0 addon release, its existing native partner
   mappings retain their previous Python search/IGNORECASE or casefold behavior.
   No trigger is changed. **Simplify Recognized Prefix Rule** converts only
   literal anchored prefixes that can be represented without losing meaning.
   Other expressions remain advanced, with their original definition retained.
9. For migration FROM 18.0, read `MIGRATION_ES.md` before running OpenUpgrade.
   The addon recovers original scopes/restrictions from snapshots and the
   migration's legacy mapping link. It cannot fix an exception during account's
   earlier migration phase. Original mappings/models are not deleted.
10. Historical imports require explicit legacy opt-in and a verified extraction
    pattern. The addon identifies partners; Odoo/OCA still control selection of
    outstanding payments and reconciliation.
11. Proposal selection also enforces the readable partner criterion: outgoing
    N43 transfers use the extracted beneficiary; CORE receipts use the full
    label. The neutral native `.*` is only a bridge to the Python check, not a
    replacement for the configured text. Journal, partner, company and amount
    filters remain cumulative. Odoo still excludes partner-only mapping models
    from proposals. If a counterpart account is subsequently added, the model
    becomes proposable and its retained readable criterion still applies.
