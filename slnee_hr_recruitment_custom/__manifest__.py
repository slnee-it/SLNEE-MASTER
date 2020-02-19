# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
{
    'name': "Human Resource Recruitment Custom",

    'summary': """
        Middle East Human Resource Recruitment Custom""",

    'description': """
    Middle East Human Resource Recruitment""",

    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Human Resources',
    'version': '1.0',
    'sequence': 20,
    'depends': ['slnee_hr_exp_info','slnee_hr_job_requisition', 'survey', 'res_documents'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/hr_recruitment_data.xml',
        'views/hr_recruitment_custom_view.xml',
        'register_qweb_report.xml',
        'report/confirm_certificate_report_qweb.xml',
        'menu.xml',
        ],
    # only loaded in demonstration mode
    'demo': [
            'demo/hr_recruitment_demo.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
