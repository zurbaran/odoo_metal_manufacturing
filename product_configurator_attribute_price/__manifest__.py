 
{
    'name': 'Product Configurator Attribute Price',
    'version': '16.0.1.0.0',
    'summary': 'Configurador de productos con cálculo de precio personalizado',
    'description': 'Este módulo permite configurar productos individualmente, asignarles una fórmula matemática a un atributo para calcular el precio, una medida.',
    'author': 'Antonio Caballero',
    'maintainer':'Antonio Caballero',
    'website':'https://github.com/zurbaran/odoo_metal_manufacturing',
    'depends': ['sale', 'sale_product_configurator', 'product'],
    'data': [
        'views/product_template_attribute_value_view.xml',
        'views/sale_order_line_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',

}
