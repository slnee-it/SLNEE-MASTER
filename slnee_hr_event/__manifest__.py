# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Training",
    'summary': """
        Middle East Human Resource Training Module """,
    'description': """
        It handles tow type of trainings:
        1) Internal Trainings
        2) External Trainings

    Internal Trainings:

    Training department create trainings and invite attendees based on department, branch.
    Interested employees subscribe to training, based on employees department head approval
    training co-ordinate confirm subscription of employees.
    Once employee successfully complete training it automatically added to it's profile.

    External Trainings:

    Employee can request to add his/her external training details on their profile.

    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Tools',
    'version': '1.0',
    'sequence': 20,
    'depends': ['event', 'slnee_hr', 'slnee_hr_expense_management', 'hr_expense_payment'],
    'data': [
        # 'security/security.xml',
        #'data/event_data.xml',
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/event_view.xml',
        'views/hr_employee_training_view.xml',
        'data/training_operations_data.xml',
        'menu.xml',
    ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
