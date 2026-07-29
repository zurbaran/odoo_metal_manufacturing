{
    "name": "MRP Child MO Sale Propagation",
    "version": "19.0.1.0.1",
    "summary": (
        "Propaga sale_line_id y sale_id a las OF hijas y a los componentes comprados"
    ),
    "author": "Antonio Caballero",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "maintainer": "Antonio Caballero",
    "website": "https://github.com/zurbaran/odoo_metal_manufacturing",
    "depends": [
        "sale_mrp",
        "sale_purchase_stock",
    ],
    "installable": True,
    "auto_install": False,
}
