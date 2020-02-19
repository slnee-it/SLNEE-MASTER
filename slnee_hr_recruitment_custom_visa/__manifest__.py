# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Hr Recruitment Custom Visa",
    'summary': """ Hr Recruitment Custom Visa """,
    'description': """ """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['slnee_hr_recruitment_custom', 'slnee_hr_visa_recruiter'],
    'data': [
            'views/hr_recruitment_custom_visa_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
}
