# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Grade",
    'summary': """ HR Grade""",
    'description': """
         HR Grade
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['slnee_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_grade_view.xml',
    ],
    'price': 10,
    'currency': 'EUR',
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    'installable': True,
    'auto_install': False,
}
