# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Employee Profile Information",
    'summary': """ Employee Profile Information""",
    'description': """
        Employee Profile Information About Experience, Qualification And Certification
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': ['slnee_hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/email_template_view.xml',
        'views/employment_reference_report.xml',
        'views/employee_view.xml',
        ],
    # only loaded in demonstration mode
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}