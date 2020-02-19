# -*- coding: utf-8 -*-
{
    'name': "payment_control",

    'summary': """
        Control Payment to prevent issueing payment over the partner limit
        """,

    'description': """
        This module is built to manage and control issueing Payment so as to prevent issueing payment over the partner limit
    """,

    'author': "Slnee",
    'website': "http://www.slnee.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}