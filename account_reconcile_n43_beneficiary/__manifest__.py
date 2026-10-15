# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "N43 Beneficiary Partner Resolution",
    "summary": "Resolve outgoing N43 beneficiaries through OCA partner mappings",
    "version": "19.0.1.1.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Antonio Caballero",
    "maintainer": "Antonio Caballero",
    "website": "https://github.com/zurbaran/odoo_metal_manufacturing",
    "depends": [
        "account_reconcile_oca",
        "l10n_es_account_statement_import_n43",
    ],
    "data": [
        "views/account_journal_views.xml",
        "views/account_reconcile_model_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
