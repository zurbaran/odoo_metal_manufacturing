{
    "name": "Binary download fix for AEAT BOE exports",
    "version": "18.0.1.0.0",
    "category": "Technical",
    "summary": """Corrige la descarga de campos binarios
      (BOE AEAT y similares) en Odoo 18""",
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
