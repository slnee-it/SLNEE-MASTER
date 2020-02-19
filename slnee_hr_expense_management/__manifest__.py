# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Advance Expense Management',
    'summary': """
        Middle East Human Resource Advance Expenses Management """,
    'version': '1.0',
    'sequence': 20,
    'category': 'Human Resources',
    'description': """
        Expense is related to every operation with reimbursment, deduction and company contribution facility.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'images': [],
    'depends': ['hr_expense', 'hr_payroll', 'sales_team', 'hr_admin'],#'slnee_hr_admin'],
    'data': [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/hr_expense_view.xml",
        'menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
