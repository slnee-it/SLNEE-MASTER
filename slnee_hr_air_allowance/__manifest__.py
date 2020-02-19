# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Air Allowance",
    'summary': """ HR Air Allowance """,
    'description': """
     By this module we can calculate the air allowances, deduct the amount from employee payslip
     """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Generic Modules/Human Resources',
    'version': '1.0',
    'depends': ['hr_payroll', 'slnee_hr_contract', 'slnee_hr_dependent'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'views/air_allowance_view.xml',
        'report/empcontract_report_qweb.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}
