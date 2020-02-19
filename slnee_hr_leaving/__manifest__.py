# Part of odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "HR Leaving",
    'summary': """ HR Leaving """,
    'description': """
        HR Leaving
    """,
    'author': 'SLNEE',
    'website': "http://www.slnee.com",
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': [
        'base',
        'hr_payroll_account',
        'slnee_hr_leaves_management',
        'account_voucher',
        'slnee_hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/leaving_email_template_data.xml',
        'data/hr_leaving_data.xml',
        'views/hr_employee_leaving_view.xml',
    ],
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