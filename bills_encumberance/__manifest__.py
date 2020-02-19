# -*- coding: utf-8 -*-
{
    'name': "bills_encumberance",

    'summary': """
        This module to integrate vendor bills with encumberance orders
        
        """,

    'description': """
        This module to integrate vendor bills with encumberance orders
        
    """,

    'author': "Slnee",
    'website': "http://www.slnee.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','budget_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}