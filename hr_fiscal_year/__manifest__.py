# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "HR Fiscal Year",
    'summary': """ HR Fiscal Year """,
    'description': """ Calendar Year For Public Holiday Duration and Year period""",
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['hr', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_fiscal_year_view.xml',
        'menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
}
