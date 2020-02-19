# -*- coding: utf-8 -*-

{
    'name': 'BKC Payment Encumbrance Integration',
    'category': 'Accounting',
    'sequence': 0,
    'description': """
Integrate account payment order with Encumbrance order and budget
--------------------------------------------------------------
""",
    'depends': ['account_payment','slnee_budget','slnee_correlation_order'],
    'data': [
        'data/encumberance_sequence.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/payment_correlation_views.xml',
        'views/res_config_settings_views.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}