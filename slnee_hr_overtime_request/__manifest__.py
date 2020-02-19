# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'HR Overtime Request',
    'summary': 'HR Overtime Request',
    'version': '1.0',
    'sequence': 20,
    'category': 'HR',
    'description': """
        In analytic overtime request company head manager will send to employee request for the overtime for few hours, and send mail about the request then after employee validate it and overtime request done
employee also can send response by mail in overtime response.

    """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'depends': ['hr', 'hr_attendance', 'mail'],
    'data': [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/analytic_overtime_request_view.xml",
        "views/menu.xml",
    ],
    'demo': [],
    'price': 0,
    'currency': "EUR",
    'installable': True,
    'auto_install': False,
}
