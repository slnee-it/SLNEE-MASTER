# -*- coding: utf-8 -*-

{
    'name': "Slnee HR Dashboard",
    'version': '1.0',
    'summary': """HR Dashboard""",
    'description': """HR Dashboard""",
    'category': 'Human Resources',
    'author': 'SLNEE',
    'website': "https://www.slnee.com",
    'depends': [
        'hr',
        'hr_holidays',
        'hr_payroll',
        'hr_attendance',
        # 'hr_timesheet_attendance',
        'hr_recruitment',
        'hr_expense',
        'slnee_hr',
        # 'slnee_hr_loan',
        'event',
    ],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/ir.model.access.csv',
        'report/broadfactor.xml',
        'views/dashboard_views.xml',
    ],
    'qweb': ["static/src/xml/hrms_dashboard.xml"],
    'images': ["static/description/banner.gif"],
    'installable': True,
    'application': True,
}
