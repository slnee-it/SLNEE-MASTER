# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Slnee HR: GOSI Contribution",
    'summary': """Slnee HR GOSI Contribution""",
    'description': """
        By this module we can calculate GOSI of employee and can deduct the amount from employee payslip.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': ['slnee_hr','hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/hr_payroll_data.xml',
        'views/hr_employee_gosi_view.xml',
        'views/hr_payroll_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/employee_gosi_demo.xml',
    ],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 250.0,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}
