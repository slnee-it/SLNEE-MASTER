# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Slnee HR Branch",
    'summary': """ Middle East Human Resource """,
    'description': """
            Middle East Human Resource Groups Configuration
        """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'sequence': 20,
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_branch_view.xml',
        'views/res_config_setting_view.xml',
        'menu.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/office_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
