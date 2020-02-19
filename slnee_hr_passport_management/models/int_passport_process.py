# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import time


class IntPassportProcess(models.Model):
    _name = 'int.passport.process'
    _inherit = 'mail.thread'
    _description = "Internal Passport process"

#     _track = {
#         'state': {
#             'slnee_hr_passport_management.mt_internal_passport_process_confirm': lambda self: self.state == 'confirm',
#             'slnee_hr_passport_management.mt_internal_passport_process_approve': lambda self: self.state == 'approve',
#             'slnee_hr_passport_management.mt_passport_submit': lambda self: self.state == 'submit',
#             'slnee_hr_passport_management.mt_internal_passport_process_cancel': lambda self: self.state == 'cancel',
#         },
#         'stage_id': {
#             'slnee_hr_passport_management.mt_internal_passport_process_stage': lambda self: self.state not in ['confirm', 'approve', 'submit', 'cancel'],
#         },
#     }

    @api.multi
    @api.depends('employee_id')
    def name_get(self):
        """
            to use retrieving the name, combination of `id & name`
        """
        res = []
        if self.employee_id:
            name = self.employee_id and self.employee_id.name or ''
            res.append((self.id, name))
        return res

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state in ['approve', 'submit']:
                raise UserError(_('You can not delete record in this stage!'))
        return super(IntPassportProcess, self).unlink()

    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self:self.env.user.id)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    note = fields.Text(string='Description')
    passport_no = fields.Char(string='Passport No', size=50, help='Passport number.')
    store_branch_id = fields.Many2one('hr.branch', string='Office', help='Passport store branch.', copy=False)
    loker = fields.Char(string='Locker', copy=False)
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    submit_date = fields.Date(string='Submitted Date', readonly=True, copy=False)
    approve_by = fields.Many2one('res.users', string='Approve By', copy=False)
    approve_date = fields.Datetime(string='Approve Date', copy=False)
    reason = fields.Selection([('passport_renewal', 'Passport Renewal'),
                               ('address_change', 'Address Change'),
                               ('adding_spouse_name', 'Adding Spouse Name'),
                               ('annual_vacation', 'Annual Vacation'),
                               ('business_trip', 'Business Trip'),
                               ('others', 'Others')], string='Reason')
    other_reason = fields.Text(string="Other Reason")
    state = fields.Selection([('draft', 'Draft'),
        ('confirm', 'Confirm'), ('approve', 'Approved'),
        ('submit', 'Submitted'), ('cancel', 'Cancel'),
        ('set_to_draft', 'Set To Draft')], default='draft')

    @api.constrains('date_from', 'date_to')
    def _check_mobile_number(self):
        """
            to use add constraint on mobile_number
        """
        for obj in self:
            if obj.date_from > obj.date_to:
                raise UserError(_('Invalid Date! Please enter valid duration from and to date!'))
        return True

    @api.multi
    def _track_subtype(self, init_values):
        """
            to use track on state
        """
        if 'state' in init_values and self.state == 'confirm':
            return 'slnee_hr_passport_management.mt_internal_passport_process_confirm'
        elif 'state' in init_values and self.state == 'approve':
            return 'slnee_hr_passport_management.mt_internal_passport_process_approve'
        elif 'state' in init_values and self.state == 'submit':
            return 'slnee_hr_passport_management.mt_passport_submit'
        elif 'state' in init_values and self.state == 'cancel':
            return 'slnee_hr_passport_management.mt_internal_passport_process_cancel'
#         if 'stage_id' in init_values and self.state not in ['confirm', 'approve', 'submit', 'cancel']:
#             return 'slnee_hr_passport_management.mt_internal_passport_process_stage'
        return super(IntPassportProcess, self)._track_subtype(init_values)

    @api.onchange('date_to')
    def onchage_expiration_date(self):
        """
            set the value onchange of expiration_date
        """
        if self.date_from and self.date_to and self.date_from >= self.date_to:
            raise UserError(_('Invalid Date! Please enter valid duration from and to date!'))

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            set the value onchange of employee_id
        """
        if not self.employee_id:
            self.passport_no = False
        else:
            self.passport_no = False
            doc_type = self.env['res.document.type'].search([('code', '=', 'pno')])
            for doc in self.employee_id.document_ids:
                if doc.type_id == doc_type[0]:
                    self.passport_no = doc.doc_number

    @api.model
    def create(self, vals):
        """Overwrite the create method to add the passport process"""
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            doc_type = self.env['res.document.type'].search([('code', '=', 'pno')])
            passport_no = False
            for doc in employee.document_ids:
                if doc.type_id == doc_type[0]:
                    passport_no = doc.doc_number
            vals.update({'passport_no': passport_no})
        return super(IntPassportProcess, self).create(vals)

    @api.multi
    def write(self, vals):
        """Overwrite the write method to change value of the passport process"""
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            doc_type = self.env['res.document.type'].search([('code', '=', 'pno')])
            passport_no = False
            for doc in employee.document_ids:
                if doc.type_id == doc_type[0]:
                    passport_no = doc.doc_number
            vals.update({'passport_no': passport_no})
        return super(IntPassportProcess, self).write(vals)

    @api.multi
    def act_confirm(self):
        """
            set the confirm state
        """
        document_id = self.env['res.documents'].search([('employee_id', '=', self.employee_id.id), ('doc_number', '=', self.passport_no), ('status', '=', 'office')])
        if not document_id:
            raise UserError(_('Passport is not registered by this employee , please contact his HR manger!'))
        self.state = 'confirm'

    @api.multi
    def act_approve(self):
        """
            set the approve state
        """
        document_ids = self.env['res.documents'].search([('employee_id', '=', self.employee_id.id), ('doc_number', '=', self.passport_no)])
        for document_id in document_ids:
            document_id.status = 'gr_user'
        self.write({'state': 'approve', 'approve_by': self.env.user.id, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        self.message_subscribe_users(user_ids=self.env.user.id)

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

    @api.multi
    def act_submit(self):
        """
            set the submit state
        """
        register_ids = self.env['emp.passport.register'].search([('employee_id', '=', self.employee_id.id), ('passport_no', '=', self.passport_no)])
        document_ids = self.env['res.documents'].search([('employee_id', '=', self.employee_id.id), ('doc_number', '=', self.passport_no)])
        for register_id in register_ids:
            body = "Passport Is Relocate from office %s Locker Number %s to office %s Locker Number %s" % (register_id.store_branch_id.name, register_id.loker, self.store_branch_id.name, self.loker)
            register_id.message_post(message_type="email", subtype='mail.mt_comment', body=_(body))
            register_id.write({'store_branch_id': self.store_branch_id.id, 'loker':self.loker})
        for document_id in document_ids:
            document_id.write({'position': '/'.join([self.store_branch_id.name, self.loker]),
                               'status': 'office'})
        mail_msg_obj = self.env['mail.message']
        message_body = """Hello %s,<br/><br/>

                        Passport %s of employee %s is submitted to office %s in locker number %s.<br/><br/>

                        Regards,<br/>
                        %s""" % (self.approve_by.partner_id.name, self.passport_no
                            , self.employee_id.name, self.store_branch_id.name,
                            self.loker, self.env.user.name)
        vals = {'subject': "Notification For Passport Submission",
                'body': message_body,
                'message_type': 'comment',
                'partner_ids': [(6, 0, [self.approve_by.partner_id.id])],
                'model': 'int.passport.process',
                'res_id': self.id,
            }
        mail_mail_record = self.env['mail.mail'].create(vals)
        mail_msg_record = mail_msg_obj.browse(mail_mail_record.mail_message_id.id)
        mail_msg_record.write({'partner_ids': [(6, 0, [self.approve_by.partner_id.id])], }) # 'notification_ids': [(0, 0, [self.approve_by.partner_id.id])]})
        self.write({'state': 'submit', 'submit_date': time.strftime('%Y-%m-%d')})
