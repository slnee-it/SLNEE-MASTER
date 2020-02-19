# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Copy Center Process",
    'summary': """ HR Copy Center Process """,
    'description': """
        Copy center – if any employee wants to generate hard copies of any official document then here they will select
        type of papers & number of copies and then at last related employee expense will be generated.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['product', 'hr_expense_payment'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/hr_copy_center_view.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}
