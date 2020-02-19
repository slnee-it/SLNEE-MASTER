# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployeeTraining(models.Model):
    _name = 'hr.employee.training'
    _inherit = 'mail.thread'
    _description = 'HR Employee Training'

    name = fields.Char('Training Summary', size=32, required=True, help="Name of the Training")
    employee_id = fields.Many2one('hr.employee', 'Employee', default=lambda self: self.env['hr.employee'].get_employee(), required=True)
    job_id = fields.Many2one('hr.job', readonly=True, string='Job Position')
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    type = fields.Selection([('internal', 'Internal'), ('external', 'External')], 'Type of Training', required=True, default="external")
    start_date = fields.Datetime('Start Date', required=True)
    end_date = fields.Datetime('End Date', required=True)
    place = fields.Char('Training Place', size=32)
    description = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('validate', 'Attended'), ('approve', 'Approved'), ('refuse', 'Refused')], 'Status', track_visibility='onchange', default="draft")
    approved_date = fields.Datetime('Approved Date', readonly=True, track_visibility='onchange', copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, track_visibility='onchange', copy=False)
    total_hours = fields.Float('Total Hours', default=0.0,)
    category = fields.Many2one('event.type', 'Training Category', states={'done': [('readonly', True)]})

    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_start_dates(self):
        """
            Check start and end dates.
        """
        for training in self.read(['start_date', 'end_date']):
            if training['start_date'] and training['end_date'] and training['start_date'] > training['end_date']:
                raise UserError(_('Error! Start Date must be less than End Date.'))

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
            Set department, job and employee code according to employee.
        """
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id

    @api.model
    def create(self, values):
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id,
                           'job_id': employee.job_id.id})
        return super(HrEmployeeTraining, self).create(values)

    @api.multi
    def write(self, values):
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id})
        return super(HrEmployeeTraining, self).write(values)

    @api.multi
    def unlink(self):
        for training in self:
            if training.state not in ['draft', 'refuse']:
                raise UserError(_('You cannot delete a external training which is not in draft or refuse!'))
        return super(HrEmployeeTraining, self).unlink()

    @api.multi
    def confirm_training(self):
        """
            Change state to confirm and send message to employee.
        """
        self.ensure_one()
        hr_groups_config_obj = self.env['hr.groups.configuration']
        hr_groups_config_ids = hr_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id),
                                                            ('talent_acquisition_ids', '!=', False)])
        user_ids = hr_groups_config_ids and [employee.user_id.id for employee in hr_groups_config_ids.talent_acquisition_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids=user_ids)
        self.state = 'confirm'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Training Confirmed.'))

    @api.multi
    def approve_training(self):
        """
            Change state to approve and send message.
        """
        self.ensure_one()
        self.state = 'approve'
        self.approved_by = self.env.uid
        self.approved_date = datetime.today()
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Training Waiting Approval.'))

    @api.multi
    def refuse_training(self):
        """
            Change state to refuse and send message.
        """
        self.ensure_one()
        self.state = 'refuse'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Training Refused'))

    @api.multi
    def validate_training(self):
        """
            Change state to validate and send message.
        """
        self.ensure_one()
        self.state = 'validate'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Training Approved.'))

    @api.multi
    def set_to_draft(self):
        """
            Change state to draft and send message.
        """
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Training Created.'))


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _compute_training_count(self):
        if not self.user_has_groups('event.group_event_user'):
            return
        for employee in self:
            employee.event_count = self.env['hr.employee.training'].search_count([('employee_id', 'child_of', employee.ids)])

    event_count = fields.Integer("Events", compute='_compute_training_count', help="Number of events the employee has participated.")
    training_ids = fields.One2many('hr.employee.training', 'employee_id', 'Trainings')

    @api.multi
    def action_training_view(self):
        action = self.env.ref('slnee_hr_event.action_employee_training').read()[0]
        action['context'] = {}
        action['domain'] = [('employee_id', 'child_of', self.ids)]
        return action