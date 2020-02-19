# -*- coding: utf-8 -*-

{
    'name': 'BKC Security',
    'summary': 'Security',
    'description': """
BKC Security
--------------------------------------------------------------
Adding new security category and groups
""",
    'depends': ['account_budget',' hr_base' , 'hr_attendance', 'hr_payroll'],
    'data': [
        'security/slnee_security.xml',
        'views/menus.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
