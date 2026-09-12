{
    "name": "Product Configurator Attribute Price",
    "version": "19.0.5.4.0",
    "category": "Manufacturing",
    "summary": """Configura precios dinámicos con fórmulas en atributos de producto""",
    "author": "Antonio Caballero",
    "maintainer": "Antonio Caballero",
    "website": "https://github.com/zurbaran/odoo_metal_manufacturing",
    "depends": ["sale", "product"],
    "data": [
        "views/product_template_attribute_value_view.xml",
        "views/sale_order_line_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "license": "AGPL-3",
}
