# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Warning',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Employee Salary, Employees Details',
    'description': "",
    'author': 'SLNEE',
    'website': 'www.slnee.com',
    'depends': [
        'mail',
        'slnee_hr_payroll',
    ],
    'data': [
        # 'security/hr_security.xml',
        'security/ir.model.access.csv',
        'data/warning.xml',
        'data/warning_types.xml',
        'data/mail_template.xml',
        'views/issue_warning.xml',
        'views/warning_type_view.xml',
        'views/hr_view.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
