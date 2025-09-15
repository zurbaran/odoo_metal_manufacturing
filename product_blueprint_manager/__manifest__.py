{
    "name": "Product Blueprint Manager",
    "version": "16.0.10.1.5",
    "category": "Manufacturing",
    "summary": (
        "Gestione planos de productos y genere documentos de forma dinámica. "
        "Este módulo permite la gestión de planos de productos, incluyendo "
        "la vinculación de documentos característicos y la generación de "
        "documentos dinámicos con fórmulas integradas basadas en atributos de "
        "producto."
    ),
    "author": "Antonio Caballero",
    "maintainer": "Antonio Caballero",
    "website": "https://github.com/zurbaran/odoo_metal_manufacturing",
    "depends": [
        "product",
        "sale",
        "sale_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "reports/report_paperformat.xml",
        "data/blueprint_report_data.xml",
        "views/product_blueprint_condition_views.xml",
        "views/sale_order_views.xml",
        "views/product_views.xml",
        "views/product_blueprint_views.xml",
        "views/product_blueprint_formula_views.xml",
        "views/menu.xml",
        "reports/sale_order_report.xml",
        "reports/purchase_order_report.xml",
        "reports/blueprint_report.xml",
    ],
    "installable": True,
    "application": True,
    "license": "AGPL-3",
}
