{
    "name": "Product Configurator Attribute Price",
    "version": "18.0.4.2.1",
    "category": "Manufacturing",
    "summary": """Extiende la configuración de atributos en productos con cálculos
      dinámicos de precios
        Permite configurar productos con incrementos de precio basados en fórmulas:
        - Atributos personalizados (custom_value)
        - Incrementos fijos nativos (price_extra)
        - Incrementos acumulativos (price_so_far)
    """,
    "author": "Antonio Caballero",
    "maintainer": "Antonio Caballero",
    "website": "https://github.com/zurbaran/odoo_metal_manufacturing",
    "depends": ["sale", "sale_product_configurator", "product"],
    "data": [
        "views/product_template_attribute_value_view.xml",
        "views/sale_order_line_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "license": "AGPL-3",
}
