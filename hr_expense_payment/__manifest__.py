# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Employee Expense Reimbursement in Monthly Salary",
    'summary': "Employee Expense Reimbursement in Monthly Salary",
    'description': """
To paying employees back in the mohtly salary when they spend their own money while working on company time. These expenses generally occur when an employee is traveling for business.
""",
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['decimal_precision', 'hr_expense', 'hr_admin', 'hr_payroll'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'views/hr_expense_payment_view.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 50.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: