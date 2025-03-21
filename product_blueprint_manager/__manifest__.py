{
    'name': 'Product Blueprint Manager',
    'version': '17.0.4.0.0',
    'category': 'Manufacturing',
    'summary': 'Gestione planos de productos y genere documentos de forma dinámica.',
    'description': '''
        Este módulo permite la gestión de planos de productos, incluyendo
        la vinculación de documentos característicos y la generación de documentos dinámicos
        con fórmulas integradas basadas en atributos de producto.
    ''',
    'author': 'Antonio Caballero',
    'maintainer': 'Antonio Caballero',
    'website': 'https://github.com/zurbaran/odoo_metal_manufacturing',
    'depends': ['product', 'sale', 'sale_management', 'product_configurator_attribute_price'],
    "data": [
        "security/ir.model.access.csv",
        "reports/report_paperformat.xml",
        "data/blueprint_report_data.xml",
        "views/product_views.xml",
        "views/menu.xml",
        "reports/sale_order_report.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
