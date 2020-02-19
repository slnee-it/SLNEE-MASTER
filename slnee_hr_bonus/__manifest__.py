# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Employee Bonus",
    'summary': """ Employee Bonus Calculation """,
    'description': """ Employee Bonus Calculation """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['hr_payroll', 'hr_fiscal_year', 'slnee_hr', 'hr_warning'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/report.xml',
        'data/hr_payroll_data.xml',
        'data/mail_template_data.xml',
        'views/bonus_view.xml',
        'views/res_company_view.xml',
        'report/report_employee_promotion.xml',
        'report/report_employee_no_promotion.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    'price': 0.0,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
