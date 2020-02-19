# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_states = [('draft', 'Draft'), ('confirm', 'Waiting Approval'), ('approve', 'Approved'), ('done', 'Done'),
           ('refuse', 'Refused')]


class EmployeeProbationReview(models.Model):
    _name = 'emp.probation.review'
    _description = 'Employee Probation Review'
    _order = 'id desc'
    _inherit = ['mail.thread']

    @api.one
    @api.depends('join_date', 'extend_end_date', 'employment_status')
    def compute_date(self):
        """
            set probation complete date and extend date
        """
        if self.join_date and isinstance(self.join_date, str):
            join_date = datetime.strptime(self.join_date, DEFAULT_SERVER_DATE_FORMAT)
            probation_complete_date = join_date + relativedelta(months=3)
            self.probation_complete_date = probation_complete_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        extend_start_date = datetime.today() + relativedelta(days=1)
        if self.employment_status == 'extend':
            self.extend_start_date = extend_start_date
        if self.extend_end_date:
            self.probation_complete_date = self.extend_end_date

    # Fields Employee Probation Review
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    job_id = fields.Many2one('hr.job', readonly=True, string='Job Position')
    branch_id = fields.Many2one('hr.branch', 'Office', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    line_manager_id = fields.Many2one('hr.employee', string='Manager', required=True, readonly=True)
    hof_id = fields.Many2one('hr.employee', string='Head of Function', readonly=True)
    join_date = fields.Date(string='Join Date', readonly=True, required=True)
    extend_start_date = fields.Date(string='Extend Start Date')
    extend_end_date = fields.Date(string='Extend End Date')
    probation_complete_date = fields.Date(string='Probation Complete Date', compute='compute_date', store=True, readonly=True)
    probation_plan = fields.Html(string='Probation Plan', required=True)
    review = fields.Html(string='Review')
    approved_date = fields.Datetime(string='Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True, copy=False)
    state = fields.Selection(_states, string='Status', default='draft', track_visibility='onchange')
    employment_status = fields.Selection([('end', 'Probation End'),
                                          ('relieve', 'Relieve'),
                                          ('extend', 'Extend Probation')], 'Employment Status')
    rating = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),
                               ('9', '9'), ('10', '10')], string="Progress Rate", index=True)

    @api.multi
    def send_probation_mail(self):
        """
            This function send mail to employee about his/her probation status
        """
        self.ensure_one()
        if self.employment_status == 'extend':
            try:
                template_id = self.env.ref('slnee_hr_probation.email_template_probation_extend')
            except ValueError:
                template_id = False
        elif self.employment_status == 'end':
            try:
                template_id = self.env.ref('slnee_hr_probation.email_template_probation_end')
            except ValueError:
                template_id = False
        else:
            try:
                template_id = self.env.ref('slnee_hr_probation.email_template_employee_relieving')
            except ValueError:
                template_id = False
        template_id.send_mail(self.id)

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            Onchange the value based on selected employee,
            Hof, manager, job, department, company, join date, contract
        """
        self.hof_id = False
        self.line_manager_id = False
        self.job_id = False
        self.department_id = False
        self.join_date = False
        self.contract_id = False
        self.branch_id = False
        if self.employee_id:
            self.hof_id = self.employee_id.parent_id.id
            self.line_manager_id = self.employee_id.coach_id.id
            self.job_id = self.employee_id.job_id.id
            self.branch_id = self.employee_id.branch_id.id or False
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            self.join_date = self.employee_id.date_of_join
            self.contract_id = self.employee_id.contract_id.id

    @api.model
    def create(self, values):
        """
            Create a new record
            :param values: update values
        """
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id,
                           'company_id': employee.company_id.id,
                           'join_date': employee.date_of_join,
                           'contract_id': employee.contract_id.id,
                           'branch_id': employee.branch_id.id,
                           })
        return super(EmployeeProbationReview, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'hof_id': employee.coach_id.id,
                           'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id,
                           'company_id': employee.company_id.id,
                           'join_date': employee.date_of_join,
                           'contract_id': employee.contract_id.id,
                           'branch_id': employee.branch_id.id,
                           })
        return super(EmployeeProbationReview, self).write(values)

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'confirm', 'approve', 'done', 'refuse' states
        """
        for record in self:
            if record.state in ['confirm', 'approve', 'done', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (record.state))
        return super(EmployeeProbationReview, self).unlink()

    @api.multi
    def name_get(self):
        """
            to use retrieving the employee name
        """
        result = []
        for review in self:
            name = review.employee_id.name or ''
            result.append((review.id, name))
        return result

    @api.multi
    def review_confirm(self):
        """
            sent the status of his/her probation in confirm state
        """
        self.ensure_one()
        if self.employee_id and self.employee_id.parent_id and self.employee_id.parent_id.user_id:
            self.message_subscribe_users(user_ids=[self.employee_id.parent_id.user_id.id])
        self.message_post(message_type="email", subtype='mail.mt_comment',
                          body=("Employee Probation Review Request Confirmed."))
        self.state = 'confirm'

    @api.multi
    def review_done(self):
        """
            sent the status of his/her probation in done state
        """
        self.ensure_one()
        probation_complete_date = datetime.strptime(self.probation_complete_date, DEFAULT_SERVER_DATE_FORMAT)
        date = probation_complete_date - timedelta(days=10)
        today_date = date.today()
        if today_date >= date and today_date <= probation_complete_date:
            self.state = 'done'
            if self.employment_status == 'end':
                self.employee_id.employee_status = 'active'
        else:
            raise ValidationError(_("Today's date must be 10 days less then Probation Complete Date"))

    @api.multi
    def review_approve(self):
        """
            sent the status of his/her probation in approve state
        """
        self.ensure_one()
        self.write({'state': 'approve', 'approved_by': self.env.uid, 'approved_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment',
                          body=("Employee Probation Review Request Approved."))

    @api.multi
    def review_refuse(self):
        """
            sent the status of his/her probation in refuse state
        """
        self.ensure_one()
        self.state = 'refuse'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=("Employee Probation Review Request Refused."))

    @api.multi
    def set_draft(self):
        """
            sent the status of his/her probation in draft state
        """
        self.ensure_one()
        self.state = 'draft'
        self.approved_by = False
        self.approved_date = False
        self.message_post(message_type="email", subtype='mail.mt_comment', body=("Employee Probation Review Request Created."))
