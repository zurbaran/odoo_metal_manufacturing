{
    "name": "Binary download fix for AEAT BOE exports (innecesario)",
    "version": "18.0.1.0.1",
    "category": "Technical",
    "summary": "INNECESARIO en Odoo/OCA 18.0 actualizados; ver VALIDATION.md",
    "author": "Antonio Caballero",
    "license": "AGPL-3",
    "maintainer": "Antonio Caballero",
    "website": "https://github.com/zurbaran/odoo_metal_manufacturing",
    "depends": [
        "web",
        "l10n_es_aeat",
    ],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "web_binary_boe_download_fix/static/src/js/boe_binary_download_patch.esm.js",
        ],
    },
    "installable": True,
    "application": False,
}
