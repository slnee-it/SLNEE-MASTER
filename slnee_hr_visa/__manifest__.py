# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Employee Visa",
    'summary': """HR Employee Visa """,
    'description': """
         VISA request – Here employee will request for VISA & and then VISA will get approved by officer.
        > Family Visa Request
        > New Visa Request
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': ['hr_expense_payment', 'res_documents', 'slnee_hr_grade'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/gr_operation_data.xml',
        'views/hr_visa_view.xml',
        'menuitem.xml',
        'report/visit_visa.xml',
        'report/embassy_visit_visa.xml',
        'report/business_visa.xml',
    ],
    'demo': [
        'demo/visa_demo.xml',
    ],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}
