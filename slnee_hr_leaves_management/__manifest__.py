# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Middle East Human Resource Leaves Management',
    'category': 'Human Resources',
    'version': '1.0',
    'sequence': 20,
    'description': """
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'images': [],
    'depends': [
        'hr_holidays', 'hr_attendance', 'slnee_hr', 'slnee_hr_contract', 'hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/resource_calender_data.xml',
        'data/hr_holiday_status_data.xml',
        'data/hr_payroll_data.xml',
        'data/hr_holidays_data.xml',
        'views/hr_public_holidays_view.xml',
        'views/hr_holidays_view.xml',
        'wizard/leaves_allocation_view.xml',
        'views/hr_payroll_view.xml',
        'menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
