# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Accomodation Booking",
    'summary': """ HR Accomodation Booking """,
    'description': """
        Employee can register accomdation details and after this generate expense.
        """,
    'author': 'SLNEE',
    'website': 'http://www.slnee.com',
    'category': 'HR',
    'version': '1.0',
    'depends': ['hr_admin', 'hr_expense_payment'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/hr_admin_operations_data.xml',
        'data/product_data.xml',
        'views/accomodation_view.xml',
        'wizard/admin_reports_view.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: