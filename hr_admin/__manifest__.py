# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Admin",
    'summary': "HR Admin",
    'description': """
Allow specific user to perform 'HR Admin' related works and also this kind of users have no access to see other employee's records""",
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['slnee_hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/admin_reports_view.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 30.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}
