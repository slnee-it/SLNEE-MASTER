# Copyright 2018 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'HR Timesheet Sheet',
    'version': '11.0.1.0.1',
    'category': 'Human Resources',
    'sequence': 80,
    'summary': 'Timesheet Sheets, Activities',
    'license': 'AGPL-3',
    'author': 'SLNEE',
    'website': 'https://github.com/OCA/hr-timesheet',
    'depends': [
        'hr_timesheet',
        'web_widget_x2many_2d_matrix',
        'slnee_hr_attendance_analysis',
        'slnee_hr_overtime',
        'slnee_hr_contract',
        'hr_payroll',
        'slnee_hr_leaves_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_timesheet_sheet_security.xml',
        'data/hr_timesheet_sheet_data.xml',
        'data/hr_payroll_data.xml',
        'views/hr_timesheet_sheet_views.xml',
        'views/hr_department_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_payroll_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
