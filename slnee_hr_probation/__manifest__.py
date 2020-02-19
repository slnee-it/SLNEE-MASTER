# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Employee Probation",
    'summary': """ HR Employee Probation """,
    'description': """
        HR Employee Probation details
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['hr_recruitment', 'hr_contract', 'slnee_hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/email_template_view.xml',
        'views/hr_employee_probation_view.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 80.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}
