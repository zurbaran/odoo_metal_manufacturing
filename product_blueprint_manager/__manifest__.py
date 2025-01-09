{
    'name': 'Product Blueprint Manager',
    'version': '16.0.1.0.0',
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
    'depends': ['product', 'sale'],# 'product_configurator_attribute_price'],
    'data': [
        'views/product_views.xml',
        'views/menu_views.xml',
        'views/blueprint_report_template.xml',
        'views/sale_report_blueprint_inherit.xml',
        'data/blueprint_report_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
