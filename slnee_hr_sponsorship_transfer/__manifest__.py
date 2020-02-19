# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Sponsorship Transfer",
    'summary': """ Employee Sponsorship Transfer""",
    'description': """
       Sponsorship transfer – used to transfer sponsorship of an employee.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': ['slnee_hr'],
    'data': [
            'security/security.xml',
            'security/ir.model.access.csv',
            'data/email_template_view.xml',
            'views/hr_sponsorship_transfer_view.xml',
            ],
    # only loaded in demonstration mode
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}
