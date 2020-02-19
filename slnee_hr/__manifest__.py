# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Middle East Human Resource",
    'summary': """ Human Resource Management """,
    'description': """
        Human Resource Management specific for middle east companies
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'sequence': 20,
    'depends': ['hr_recruitment', 'slnee_hr_groups_configuration', 'mail', 'hr_fiscal_year'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/mail_channel_demo.xml',
        'views/hr_view.xml',
        'wizard/employee_head_count_report_view.xml',
        'wizard/employee_head_count_report_template.xml',
        'wizard/new_joining_report_view.xml',
        'wizard/new_joining_report_template.xml',
        'views/res_partner_view.xml',
        'views/hr_job_view.xml',
        'views/email_template_view.xml',
        'views/cron.xml',
        'views/res_company_view.xml',
        'menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/employee_demo.xml',
        # 'demo/employee_gosi_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
