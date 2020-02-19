# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Middle East Human Resource Attendances',
    'summary': """ Middle East Human Resource Attendances """,
    'version': '1.0',
    'sequence': 20,
    'category': 'Human Resources',
    'description': """
This module aims to manage employee's attendances.
==================================================

Keeps account of the attendances of the employees on the basis of the
actions(Sign in/Sign out) performed by them.
       """,
    'author': 'SLNEE',
    'website': 'https://www.odoo.com/page/employees',
    'images': [],
    'depends': ['hr_attendance', 'slnee_hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/company_view.xml',
        'views/hr_attendance_view.xml',
        'views/resource_view.xml',
        'menu.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
