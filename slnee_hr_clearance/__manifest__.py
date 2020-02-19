# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "HR Clearance",
    'summary': """ HR Clearance """,
    'description': """ """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['account', 'slnee_hr', 'survey'],
    'data': [
            'security/ir.model.access.csv',
            'data/employee_clearance_data.xml',
            'data/email_template.xml',
            'data/exit_employee_form.xml',
            'views/hr_employee_clearance_view.xml',
            'views/res_config_settings_view.xml',
            'menu.xml',
            ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
}
