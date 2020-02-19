# -*- coding: utf-8 -*-

{
    'name': 'BKC Budget Transfer',
    'category': 'Accounting',
    'sequence': 0,
    'description': """
Manage budger transfer amount between different budget lines
--------------------------------------------------------------
""",
    'depends': ['analytic','slnee_budget','slnee_security'],
    'data': [
        'data/encumberance_sequence.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/budget_transfer_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
