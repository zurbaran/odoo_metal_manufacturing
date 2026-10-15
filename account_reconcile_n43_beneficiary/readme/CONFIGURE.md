1. Install the addon with its OCA dependencies. Enable **Resolve N43 Beneficiary**
   on the bank journal. The company contact is already an account holder; add
   other actual holder contacts only when needed.
2. Check an original bank file before choosing the beneficiary concept. `2305`
   (selection `05`) is the expected CajaMar layout, not universal N43 semantics.
   Keep **N43 Partner Search = None** for the priority scenario.
3. Create an invoice matching reconciliation model per supplier, restricted to
   the journal, outgoing payments and expected partner. Require the partner.
   Leave **Auto-validate** disabled unless separately authorized.
4. In **Partner Mapping**, select **Label Match Type**, enter **Text**, choose
   the case option and select the existing partner. For example:

   | Match type | Text | Case-sensitive | Partner |
   | --- | --- | --- | --- |
   | Starts with | COREMUTUA | No | Mutua Madrileña |
   | Contains | TEMPLAGLASS | No | Templaglass S.L. |
   | Contains | VIDRIOS SALINAS | No | Vidrios Salinas, S.L. |
   | Contains | VBH | No | VBH Iberia, S.L. |

5. A **Readable Label Condition** is an additional condition on the COMPLETE
   bank label. It is not the beneficiary mapping. Set it only when needed.
   Native Contains / Not Contains remain suitable for existing ordinary
   conditions; no conversion is required to keep using them.
6. For N43 outgoing transfers, partner mapping text is evaluated against the
   extracted BENEFICIARY NAME. Document numbers never identify the supplier.
   For ordinary CORE lines, mappings see the complete label. Notes remain an
   independent advanced Python condition and are ANDed with label matching.
7. Starts with, Contains, Ends with and Exactly equals treat punctuation and
   special characters literally. Exactly equals does not accept extra text or
   a trailing newline. Advanced Python expressions retain `re.match` semantics;
   use `.*` explicitly when an advanced expression should match inside text.
   Advanced expressions control their own flags; the case checkbox is for text.
8. Existing rules stay unchanged on upgrade. **Simplify Recognized Prefix Rules**
   is an explicit action: it recognizes only proven literal prefixes, preserving
   anchors, original expressions and historical casing semantics. Complex rules
   remain advanced. Clearing a readable match type restores its archived native
   condition; review the restored condition before saving.
9. Historical N43 imports require **Also Resolve Previously Imported Lines** and
   a verified extraction pattern. No reimport or destructive backfill is needed.

Partner resolution does not enforce matching dates or exact payment amounts.
OCA controls payment suggestions. Conflicting applicable mappings leave the
partner unresolved; an explicitly selected third party is preserved.
