# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Middle East Human Resource contract",
    'summary': """ Employee Contract """,
    'description': """ Enhance the feature of base hr_contract module according to Middle East Human Resource. """,
    'author': 'SLNEE',
    'website': "http://www.slnee.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '1.0',
    'sequence': 20,

    # any module necessary for this one to work correctly
    'depends': ['account', 'slnee_hr_grade', 'hr_contract', 'hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/hr_payroll_data.xml',
        'views/contract_view.xml',
        # 'views/contract_cron.xml',
        'report/empcontract_report_qweb.xml',
        'report/newjoin_empcontract_reportqweb.xml',
        'register_qweb_report.xml',
        'menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
