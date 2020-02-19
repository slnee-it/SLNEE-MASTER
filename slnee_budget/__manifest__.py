# -*- coding: utf-8 -*-

{
    'name': 'BKC Budget Management',
    'category': 'Accounting',
    'sequence': 0,
    'description': """
Add Custom fields to budget
--------------------------------------------------------------
""",
    'depends': ['account_invoicing','analytic','account_budget'],
    'data': [
        # 'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/budget_views.xml',
        # 'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
