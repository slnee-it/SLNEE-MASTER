# -*- coding: utf-8 -*-

{
    'name': 'BKC Encumbrance',
    'category': 'Accounting',
    'sequence': 0,
    'description': """
Handle business of Encumbrance order on budget line
--------------------------------------------------------------
""",
    'depends': ['account', 'slnee_budget'],
    'data': [
        'data/encumberance_sequence.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/correlation_order_views.xml',
        # 'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}