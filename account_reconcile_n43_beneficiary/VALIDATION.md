# Validation — 2026-10-15

Python 3.12.14 and PostgreSQL 16.2; real Odoo registries and ORM, disposable local databases.

| Check                                                                         | Result                                                                                                                                |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Odoo 18 addon tests, including all 25 original tests                          | 38 passed, 0 failures/errors                                                                                                          |
| Odoo 18 with refreshed current Odoo/OCA dependency checkouts                  | 38 passed, 0 failures/errors                                                                                                          |
| Odoo 19 addon tests, including all 14 original tests                          | 36 passed, 0 failures/errors (19.0.1.1.1 proposal fix)                                                                                |
| Actual 18 addon upgrade from 18.0.1.0.0 to 18.0.1.1.0, seeded persistent rule | Passed: regex/mapping, state and automation preserved; snapshot populated                                                             |
| Actual 19 addon upgrade from 19.0.1.0.0 to 19.0.1.1.0, seeded persistent rule | Passed: old Python search/IGNORECASE and native partner line preserved; manual trigger retained                                       |
| Simulated legacy 18 mapping table + OpenUpgrade link + addon 19 recovery      | Passed in the addon suite, including separate label/note scopes, signed/absolute amounts, idempotency and preservation of source rows |
| Independent OpenUpgrade flag patch                                            | Six regression scenarios exercised; composed regex tested in Python and PostgreSQL                                                    |
| Actual patched account_reconcile_model_partner_mapping ORM function           | Passed in Odoo 19; native mapped partner created and legacy row retained                                                              |
| Repository pre-commit, modified addon files                                   | Passed in both branches                                                                                                               |

The Odoo test logger also reports setup/fixture counts; the numbers above count test methods, not setup calls.

Coverage includes case sensitivity, accented/special characters, starts/contains/ends/exact, trailing newline rejection, advanced Python regex, native SQL regex validation, CORE import-time resolution despite the skip context, N43 concept preservation, same- and cross-model conflicts, conflicting bank-account identification, explicit partners, journal/company/partner/amount restrictions and reversible conservative conversion.

## 19.0.1.1.1 proposal regression

Seven added test methods exercise the actual OCA `_get_rules()` SQL query. They
cover two suppliers without cross-proposals, mapping-only managed criteria,
criteria combined with readable labels or preserved 18.0 conditions, structured
and legacy N43 beneficiary extraction, missing structured concepts, CORE full
labels, native rules, and journal/partner/company/signed-amount restrictions.
Native partner-only models remain excluded from proposals.

The reproduction edits a counterpart account through the child ORM record. This
makes a former partner-only rule proposable through Odoo's normal computed
fields, while retaining its readable criterion; no eligibility field is forced
and no SQL query is mocked. Before the fix, the tests reported five assertion
failures from cross-supplier proposals (including two condition subcases).
After the fix, the complete 19.0 suite passes all 36 test methods.

This patch changes only 19.0. The earlier 18.0 results above were not rerun for
this patch. No production database or automation trigger was changed. Visual
validation in the reconciliation UI remains pending.

## Still pending

- Full OpenUpgrade migration of a copy of Camarbax18 to Camarbax19 with these changes.
- An original CajaMar N43 file, confirming beneficiary record 2305.
- Visual/user validation in the reconciliation UI with a real pending payment.
- Full upstream OpenUpgrade fixture suite and its CI; the proposal's helper and actual account ORM function were exercised separately.

No production database was contacted. No bank movements, existing reconciliations or automatic reconciliation settings were changed in the user's databases.

## Reviewed dependency revisions

| Repository                    | Commit                                     |
| ----------------------------- | ------------------------------------------ |
| Odoo 18                       | `ac43dda46c086552d32d41a9c7d8faba7bb17d61` |
| OCA account-reconcile 18      | `00b5908cb9629cf0c59d6270926b44a0ba761add` |
| OCA bank-statement-import 18  | `7383015d73cf60530ddd8bf3a222da7da72a333e` |
| OCA l10n-spain 18             | `78b7f8f35c54cc18d803e84fe0bdfccaec0e339c` |
| Odoo 19 (proposal regression) | `e1ed4fe077ba98ce7ac6802a43bb68242081dee9` |
| OCA account-reconcile 19      | `8fc48a4beff3203241c0f61c4d3bc15631f75a4d` |
| OCA bank-statement-import 19  | `65316c38d7a5586456bc751d8939b84f1cf0bc2e` |
| OCA l10n-spain 19             | `f04d5c17e2e4929ba466bfd73e2628991bef4d4f` |
| OpenUpgrade 19                | `47836456957cd1bc17fee921577a68d42a71f18d` |

## Reproduction

On each respective branch, use its Odoo/OCA dependencies and an empty disposable database:

```bash
odoo-bin -d n43_readable_test -i account_reconcile_n43_beneficiary \
  --test-enable --test-tags=/account_reconcile_n43_beneficiary \
  --stop-after-init --no-http --without-demo=all
```

Add the appropriate addons paths, database connection options and virtual environment for the local installation. For upgrade testing, first install the original 1.0 addon, save representative rules, replace it with 1.1 and run `-u account_reconcile_n43_beneficiary` against that disposable database. Confirm the rules and trigger/state afterwards.
