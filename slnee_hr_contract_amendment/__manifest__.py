# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Contract Amendment",
    'summary': "HR Contract Amendment",
    'description': """
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['hr_payroll', 'slnee_hr_grade','hr_warning'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/transfer_employee_view.xml',
        'menu.xml',
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
