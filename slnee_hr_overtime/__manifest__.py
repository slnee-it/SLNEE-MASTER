# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Middle East Human Resource Overtime',
    'summary': 'Middle East Human Resource Overtime',
    'version': '1.0',
    'sequence': 20,
    'category': 'Human Resource',
    'description': """
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'images': [],
    'depends': ['analytic', 'hr_contract', 'slnee_hr_attendance_analysis'],
    'data': [
        'views/hr_timesheet_sheet_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
