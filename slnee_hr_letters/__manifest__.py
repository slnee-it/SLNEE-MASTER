# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Middle East Human Resource Letters',
    'summary': 'Middle East Human Resource Letters',
    'version': '1.0',
    'sequence': 20,
    'category': 'HR',
    'description': """
        Letters are Bank Transfer, Open account, Employeement Report, Family Iqama, Mroor Report, etc.
    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'images': [],
    'depends': [
        'slnee_hr_contract'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/res_country_data.xml',
        'views/multi_reports_view.xml',
        'views/res_users_view.xml',
        'views/res_country_view.xml',
        'report/bankloan_transfer_qweb.xml',
        'report/bankloan_transfer_female_qweb.xml',
        'report/bankopen_acoount_qweb.xml',
        'report/bankopen_account_female_qweb.xml',
        'report/certificate_toapprove_qweb.xml',
        'report/family_iqama_qweb.xml',
        'report/mroor_report_qweb.xml',
        'report/house_qweb.xml',
        'report/slnee_hr_letters_whomeconcern_qweb.xml',
        'report/towhome_concern_qweb.xml',
        'report/towhom_concern_female_qweb.xml',
        'report/stamping_certificate_qweb.xml',
        'report/stamping_certificate_female_qweb.xml',
        'report/wifefrom_home_country_qweb.xml',
        'report/walid_school_qweb.xml',
        'report/saudibritish_bankloan_qweb.xml',
        'report/slnee_hr_letters_transport_qweb.xml',
        'slnee_advance_hr_report.xml',
        'menu.xml',
    ],
    'demo':[
        'demo/letters_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
