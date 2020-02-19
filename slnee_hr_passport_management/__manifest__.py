# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Middle East Human Resource Passport Management",

    'summary': """
        Middle East Human Resource Passport Management""",

    'description': """
    > Passport Management
    """,

    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'GR',
    'version': '1.0',
    'sequence': 20,
    'depends': ['base', 'slnee_hr', 'slnee_hr_visa'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/passport_data.xml',
        'view/emp_passport_register_view.xml',
        'view/emp_passport_request_view.xml',
        'view/int_passport_process_view.xml',
        'view/hr_view.xml',
        'cron.xml',
        'menu.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
