# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Employee Card",
    'summary': """ HR Employee Card """,
    'description': """
        Employee can put request for their business card, ID card and access card. HR Officer can print the ID card.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['slnee_hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/icard_report_view.xml',
        'views/hr_employee_card_view.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/employee_card_demo.xml',
    ],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}
