# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time


class EmployeePassportRegister(models.Model):
    _name = 'emp.passport.register'
    _inherit = 'mail.thread'
    _description = "Employee Passport Register"

#     _track = {
#         'state': {
#             'slnee_hr_passport_management.mt_passport_registration_confirm': lambda self: self.state == 'confirm',
#             'slnee_hr_passport_management.mt_passport_receive': lambda self: self.state == 'receive',
#             'slnee_hr_passport_management.mt_passport_registration_cancel': lambda self: self.state == 'cancel',
#         },
#         'stage_id': {
#             'slnee_hr_passport_management.mt_passport_registration_stage': lambda self: self.state not in ['confirm', 'receive', 'cancel'],
#         },
#     }

    @api.multi
    @api.depends('employee_id', 'passport_no')
    def name_get(self):
        """
            to use retrieving the name, combination of `id & name`
        """
        res = []
        if self.employee_id and self.passport_no:
            name = '-'.join([self.employee_id.name or '', self.passport_no or ''])
            res.append((self.id, name))
        return res

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state == 'receive':
                raise UserError(_('You can not delete record in this stage!'))
        return super(EmployeePassportRegister, self).unlink()

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    job_id = fields.Many2one('hr.job', string='Job Title', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    branch_id = fields.Many2one('hr.branch', string='Office', readonly=True)
    register_date = fields.Date(string='Submit Date', default=time.strftime('%Y-%m-%d'))
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user.id)
    description = fields.Text(string='Description')
    passport_no = fields.Char(string='Passport No', size=50, help='Passport number.')
    profession = fields.Char(string='Profession', copy=False)
    place_of_issue = fields.Char(string='Place of Issue', help='Passport Issued place.')
    issue_date = fields.Date(string='Issue date', help="Issue date of passport.")
    expiration_date = fields.Date(string='Expiration date', help="Expiration date of passport.")
    expiration_date_hijri = fields.Char(string='Date of Expiry(Hijri)')
    store_branch_id = fields.Many2one('hr.branch', string='Office', help='Passport store branch.')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    loker = fields.Char(string='Locker')
    state = fields.Selection([('draft', 'Draft'),
                            ('confirm', 'Confirm'),
                            ('receive', 'Received'),
                            ('cancel', 'Cancel'),
                            ('set_to_draft', 'Set To Draft')], default='draft')

    @api.multi
    def _track_subtype(self, init_values):
        """
            to use track on state
        """
        if 'state' in init_values and self.state == 'confirm':
            return 'slnee_hr_passport_management.mt_passport_registration_confirm'
        elif 'state' in init_values and self.state == 'receive':
            return 'slnee_hr_passport_management.mt_passport_receive'
        elif 'state' in init_values and self.state == 'cancel':
            return 'slnee_hr_passport_management.mt_passport_registration_cancel'
#         if 'stage_id' in init_values and self.state not in ['confirm', 'receive', 'cancel']:
#             return 'slnee_hr_passport_management.mt_passport_registration_stage'
        return super(EmployeePassportRegister, self)._track_subtype(init_values)

    @api.constrains('issue_date', 'expiration_date')
    def _check_date_number(self):
        """
            to use add constraint on check_date_number
        """
        for obj in self:
            if obj.issue_date >= obj.expiration_date:
                raise UserError(_('Invalid Expiry Date! Please enter valid date!'))
        return True

    @api.onchange('company_id')
    def onchange_company(self):
        """
            set branch False
        """
        self.store_branch_id = False

    @api.onchange('expiration_date')
    def onchage_expiration_date(self):
        """
            set the value onchange of expiration_date
        """
        if self.issue_date and self.expiration_date and self.issue_date >= self.expiration_date:
            raise UserError(_('Invalid Expiry Date! Please enter valid date!'))

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            set the value onchange of employee_id
        """
        self.job_id = self.employee_id.job_id.id or False
        self.department_id = self.employee_id.department_id.id or False
        self.branch_id = self.employee_id.branch_id.id or False

    @api.model
    def create(self, vals):
        """Overwrite the create method to add the passport register"""
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            vals.update({'job_id': employee.job_id.id or False,
                         'department_id': employee.department_id.id or False,
                         'branch_id': employee.branch_id.id or False})
        return super(EmployeePassportRegister, self).create(vals)

    @api.multi
    def write(self, vals):
        """Overwrite the write method to change value of the passport register"""
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            vals.update({'job_id': employee.job_id.id or False,
                         'department_id': employee.department_id.id or False,
                         'branch_id': employee.branch_id.id or False})
        return super(EmployeePassportRegister, self).write(vals)

    @api.multi
    def act_confirm(self):
        """
            set the confirm state
        """
        self.state = 'confirm'

    @api.multi
    def act_receive(self):
        """
            set the receive state
        """
        self.state = 'receive'
        self.message_subscribe_users(user_ids=self.env.user.id)
        doc_type = self.env['res.document.type'].search([('code', '=', 'pno')])
        for doc in self.employee_id.document_ids:
            if doc.type_id == doc_type[0]:
                doc.write({'doc_number': self.passport_no, 'issue_place': self.place_of_issue,
                    'issue_date': self.issue_date, 'expiry_date': self.expiration_date,
                    'profession': self.profession,
                    'position': self.store_branch_id.name + '/' + self.loker,
                    'hijri_expiry_date': self.expiration_date_hijri or False,
                    'status': 'office'})
                return True
        self.env['res.documents'].create({'employee_id': self.employee_id.id or False,
                    'type_id': doc_type and doc_type[0].id,
                    'doc_number': self.passport_no, 'issue_place': self.place_of_issue,
                    'issue_date': self.issue_date, 'expiry_date': self.expiration_date,
                    'position': '/'.join([self.store_branch_id.name, self.loker]),
                    'hijri_expiry_date': self.expiration_date_hijri or False,
                    'profession': self.profession, 'status': 'office'})

    @api.multi
    def act_cancel(self):
        """
            set the cancel state
        """
        self.state = 'cancel'

    @api.multi
    def act_set_to_draft(self):
        """
            set the draft state
        """
        self.state = 'draft'

    @api.model
    def send_notification(self):
        """
            send notification of passport register
        """
        register_ids = self.env['emp.passport.register'].search([])
        for obj in register_ids:
            if obj.expiration_date:
                expire_date = datetime.strptime(obj.expiration_date, "%Y-%m-%d")
                notify_date = expire_date - relativedelta(days=10)
                if datetime.today().date().strftime('%Y-%m-%d') == notify_date.strftime('%Y-%m-%d'):
                    message_body = """Hello %s,
                                    You have only '10' days remaining,, your passport Expiredate is %s,

                                    Please Renew your passport.

                                    Regards,
                                    %s""" % (obj.employee_id.name, obj.expiration_date, self.env.user.name)
                    if obj.employee_id.work_email:
                        vals = {'state': 'outgoing',
                                'subject': "Notification For Passport Expiry",
                                'body_html': message_body,
                                'email_to': obj.employee_id.work_email,
                                'email_from': 'noreply@localhost'}
                        self.env['mail.mail'].create(vals)
