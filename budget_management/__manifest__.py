# -*- coding: utf-8 -*-
{
    'name': "budget_management",

    'summary': """
	Budget management and its operations        
""",

    'description': """
	This module aims to manage the budget and all its related operations such as transfer , adjustment and encumberance . 
    """,

    'author': "Slnee",
    'website': "http://www.slnee.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_budget'],

    # always loaded
    'data': [
        'data/adjustment_sequence.xml',
        'data/encumberance_sequence.xml',
        'data/transfer_sequence.xml',
        'security/budget_groups.xml',
        'views/account_move.xml',
        'views/account_invoice.xml',
        'views/res_config_settings.xml',
        'views/views.xml',
        'views/budget.xml',
        'views/budget_position.xml',
        'views/templates.xml',
        'views/encumberance.xml',
        'views/transfer.xml',
        'views/adjustment.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
