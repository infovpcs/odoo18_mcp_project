{
    'name': 'Simple Todo',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Custom Odoo Module',
    'description': """
Simple Todo
=============
This module provides custom functionality for Odoo 18.
""",
    'author': 'Your Company',
    'website': 'https://www.example.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}