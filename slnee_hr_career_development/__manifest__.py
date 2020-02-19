# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Middle East Human Resource Career Development",
    'summary': """ Middle East Human Resource Career Development """,
    'description': """ Middle East Human Resource Career Development """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Human Resources',
    'version': '1.0',
    'sequence': 20,
    'depends': ['base', 'slnee_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_career_development_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
