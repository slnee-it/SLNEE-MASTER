# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Employee Loan Management',
    'summary': """Employee Loan Management""",
    'description': """
        Employee Loan Management also manage the installment of loan.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': ['hr_payroll', 'slnee_hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/hr_payroll_data.xml',
        'views/hr_loan_view.xml',
        'views/hr_skip_installment_view.xml',
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
