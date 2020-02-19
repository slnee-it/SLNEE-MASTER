# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo import models, fields, api, _

leaving_states = [
    ('draft', 'Draft'), ('confirm', 'Waiting Approval'),
    ('inprogress', 'In Progress'), ('done', 'Done'), ('refuse', 'Refused'), ]


class EmployeeCard(models.Model):
    _name = 'hr.employee.card'
    _inherit = ['mail.thread']
    _description = "HR Employee Card"

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'confirm', 'inprogress', 'done', 'refuse' states
        """
        for card in self:
            if card.state in ['confirm', 'inprogress', 'done', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (card.state))
        return super(EmployeeCard, self).unlink()

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    job_id = fields.Many2one('hr.job', 'Job Title', readonly=True)
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    branch_id = fields.Many2one('hr.branch', 'Office', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    card_type = fields.Selection([('access', 'Access Card'), ('business', 'Business Card'), ('id_card', 'ID Card')],
                                 'Card Type', required=True, default='access')
    card_no = fields.Char('Card No', size=15)
    reason = fields.Selection([('new_card', 'New Card'), ('replace_for_damage', 'Replace for Damaged'), ('lost_card', 'Lost Card')], 'Reason', default='new_card')
    requested_date = fields.Date('Requested Date', required=True, default=fields.Date.today())
    status = fields.Selection([('permanent', 'Permanent'), ('visitor', 'Visitor'), ('secondee', 'Secondee'),
                                ('contractor', 'Contractor'), ('consultant', 'Consultant')], 'Status')
    access_type = fields.Selection([('full', 'Full'), ('limited', 'Limited')], 'Access Type')
    period_of_stay = fields.Date('Period of Stay', size=5)
    state = fields.Selection(leaving_states, 'Status', default='draft', track_visibility='onchange')
    work_phone = fields.Char('Work Telephone', size=12)
    work_mobile = fields.Char('Work Mobile', size=12)
    work_email = fields.Char('Work Email', size=40)
    approved_date = fields.Datetime('Approved Date', readonly=True, track_visibility='onchange')
    approved_by = fields.Many2one('res.users', 'Approved By', readonly=True, track_visibility='onchange')
    refused_date = fields.Datetime('Refused Date', readonly=True, track_visibility='onchange')
    refused_by = fields.Many2one('res.users', 'Refused By', readonly=True, track_visibility='onchange')
    description = fields.Text('Description')

    @api.multi
    def card_confirm(self):
        """
            sent the status of generating card his/her card in confirm state
        """
        hr_groups_config_obj = self.env['hr.groups.configuration']
        for card in self:
            hr_groups_config_ids = hr_groups_config_obj.search(
                [('branch_id', '=', card.employee_id.branch_id.id or False), ('hr_ids', '!=', False)])
            user_ids = hr_groups_config_ids and [employee.user_id.id for employee in hr_groups_config_ids.hr_ids if
                                                 employee.user_id] or []
            card.sudo().message_subscribe_users(user_ids=user_ids)
            card.state = 'confirm'
            card.message_post(message_type="email", subtype='mail.mt_comment', body=_('Card Confirmed.'))

    @api.multi
    def card_done(self):
        """
            sent the status of generating card his/her card in done state
        """
        for card in self:
            card.state = 'done'
            card.message_post(message_type="email", subtype='mail.mt_comment', body=_('Card Done.'))

    @api.multi
    def card_inprogress(self):
        """
            sent the status of generating card his/her card in inprogress state
        """
        for card in self:
            card.write({'state': 'inprogress', 'approved_by': self.env.uid, 'approved_date': fields.Datetime.now()})
            card.message_post(message_type="email", subtype='mail.mt_comment', body=_('Card is in progress.'))

    @api.multi
    def card_refuse(self):
        """
            sent the status of generating card his/her card in refuse state
        """
        for card in self:
            card.write({'state': 'refuse', 'refused_by': self.env.uid, 'refused_date': fields.Datetime.now()})
            card.message_post(message_type="email", subtype='mail.mt_comment', body=_('Card Refused.'))

    @api.multi
    def set_draft(self):
        """
            sent the status of generating card his/her card in reset to draft state
        """
        for card in self:
            card.write({'approved_by': False, 'approved_date': False, 'refused_by': False, 'refused_date': False,
                        'state': 'draft'})
            card.message_post(message_type="email", subtype='mail.mt_comment', body=_('Card Created.'))

    @api.multi
    @api.depends('employee_id')
    def name_get(self):
        """
            to use retrieving the name, combination of `name & Card`
        """
        res = []
        if self.employee_id:
            name = self.employee_id.name or ''
            name = ''.join([name, ' Card'])
            res.append((self.id, name))
        return res

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on selected employee, job, department,
            workphone, workmobile, workemail
        """
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            self.branch_id = self.employee_id.branch_id.id or False
            if self.card_type == 'business':
                self.work_phone = self.employee_id.work_phone
                self.work_mobile = self.employee_id.mobile_phone
                self.work_email = self.employee_id.work_email

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id,
                           'company_id': employee.company_id.id,
                           'branch_id': employee.branch_id.id or False,
                           })
        return super(EmployeeCard, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id,
                           'company_id': employee.company_id.id,
                           'branch_id': employee.branch_id.id or False,
                           })
        return super(EmployeeCard, self).write(values)

    @api.multi
    def print_id_card(self):
        self.ensure_one()
        return self.env.ref('slnee_hr_card.action_report_employee_idcard').report_action(self)
