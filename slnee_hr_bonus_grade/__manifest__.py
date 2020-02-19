# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Employee Grade On Bonus",
    'summary': """ Employee bonus grade details """,
    'description': """
        Employee bonus grade details.
     """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['slnee_hr_grade', 'slnee_hr_bonus'],
    'data': [
            'views/bonus_view.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}
