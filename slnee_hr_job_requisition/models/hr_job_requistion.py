# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HRJobRequisition(models.Model):
    _name = 'hr.job.requisition'
    _inherit = ['mail.thread']
    _description = 'HR Job Requisition'
    _order = 'id desc'

    @api.multi
    @api.depends('no_of_recruitment')
    def _no_of_employee(self):
        """
            this function is used to calculate number of employee
        """
        for rec in self:
            if rec.no_of_recruitment and rec.job_id:
                rec.job_id.no_of_recruitment = rec.no_of_recruitment
                hr_emp_obj = self.env['hr.employee'].search([('job_id', '=', rec.job_id.id)])
                rec.no_of_employee = len(hr_emp_obj)
                rec.expected_employees = len(hr_emp_obj) + rec.no_of_recruitment

    @api.multi
    @api.depends('no_of_employee', 'no_of_recruitment')
    def _current_recruitment(self):
        """
            this function is used to calculate number of employee for the recruitment
        """
        for rec in self:
            no_of_curr_rec = 0
            if rec.expected_employees and rec.state != 'done':
                no_of_curr_rec = rec.expected_employees - rec.no_of_employee
                if rec.no_of_recruitment >= no_of_curr_rec:
                    rec.no_of_current_recruitment = no_of_curr_rec
                else:
                    rec.write({'expected_employees': rec.no_of_employee + rec.no_of_recruitment})
                    rec.no_of_current_recruitment = rec.expected_employees - rec.no_of_employee
                if rec.expected_employees == rec.no_of_employee:
                    rec.write({'state': 'done'})
            elif rec.state == 'done':
                rec.no_of_current_recruitment = 0
                rec.expected_employees = rec.no_of_employee
            if rec.no_of_current_recruitment < 0:
                rec.no_of_current_recruitment = 0

    # Fields HR Job Requisition
    name = fields.Char('Name', required=True, help="Name of Requisition")
    arabic_name = fields.Char('Arabic Name')
    job_id = fields.Many2one('hr.job', string='Job', required=True, help="Job for which requisition required")
    expected_employees = fields.Integer(string='Total Forecasted Employees', compute='_no_of_employee', store=True)
    no_of_employee = fields.Integer(related='job_id.no_of_employee', string="Current Number of Employees", store=True)
    department_id = fields.Many2one('hr.department', string='Department', required=False, help="Department for which requisition required")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    description = fields.Text('Job Description')
    employee_ids = fields.One2many('hr.employee', 'job_id', string='Employees', groups='base.group_user')
    requirements = fields.Text('Requirements')
    no_of_recruitment = fields.Float(string="Expected in Recruitment")
    no_of_current_recruitment = fields.Integer(compute='_current_recruitment', string="Current month Recruitment", store=True, default=0)
    approved_by_recruiter = fields.Many2one('res.users', string='Approved by Recruiter', readonly=True, copy=False)
    approved_recruiter_date = fields.Datetime('Approved by Recruiter on', readonly=True, copy=False)
    approved_hof_date = fields.Datetime('Approved by HOF on', readonly=True, copy=False)
    approved_by_hof = fields.Many2one('res.users', string='Approved by HOF', readonly=True, copy=False)
    approved_hop_date = fields.Datetime('Approved by HOP on', readonly=True, copy=False)
    approved_by_hop = fields.Many2one('res.users', string='Approved by HOP', readonly=True, copy=False)
    rejected_by = fields.Many2one('res.users', string='Rejected by', readonly=True, copy=False)
    rejected_date = fields.Datetime('Rejected on', readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Waiting Approval'),
                              ('approved1', 'First Approved'),
                              ('approved2', 'Second Approved'),
                              ('rejected', 'Rejected'),
                              ('launch', 'Launch'),
                              ('hold', 'Hold'),
                              ('done', 'Done')], string='Status', readonly=True, default='draft')
    user_id = fields.Many2one('res.users', 'User', readonly=True)

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for objects in self:
            if objects.state in ['confirm', 'approved1', 'approved2', 'done', 'launch', 'hold']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HRJobRequisition, self).unlink()

    @api.model
    def create(self, values):
        """
            Create a new record
            :param values: Current record fields data
            :return: Newly created record ID
        """
        job_id = self.search([('job_id', '=', values.get('job_id')),
            ('department_id', '=', values.get('department_id')),
            ('state', 'not in', ['launch', 'done', 'rejected']),
            ])
        if job_id:
            raise UserError(_('There is already a job requisition for this job position which is not launched yet.'))

        no_of_recruitment = values.get('no_of_recruitment', False)
        if no_of_recruitment:
            job = self.env['hr.job'].browse(values.get('job_id'))
            job.write({'no_of_recruitment': no_of_recruitment})
        res = super(HRJobRequisition, self).create(values)
        hr_emp_obj = self.env['hr.employee'].search([('job_id', '=', res.job_id.id)])
        no_of_expected = len(hr_emp_obj) + int(no_of_recruitment)
        res.write({'expected_employees': no_of_expected, 'no_of_current_recruitment': no_of_recruitment or 0})
        return res

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: Current record fields data
            :return: Current update record ID
        """
        if values.get('job_id') and values.get('department_id'):
            job_id = self.search([('job_id', '=', values['job_id']),
                ('department_id', '=', values['department_id']),
                ('state', 'not in', ['launch', 'rejected']),
                ])
            if job_id:
                raise UserError(_('There is already a job requisition for this job position which is not launched yet.'))
        no_of_recruitment = values.get('no_of_recruitment')
        if no_of_recruitment and values.get('job_id'):
            job = self.env['hr.job'].browse(values.get('job_id'))
            job.write({'no_of_recruitment': no_of_recruitment})
        res = super(HRJobRequisition, self).write(values)
        no_of_rec = 0
        if ('no_of_recruitment') in values:
            if self.state == 'draft':
                job = self.env['hr.job'].browse(self.job_id.id)
                job.write({'no_of_recruitment': no_of_recruitment})
                hr_emp_obj = self.env['hr.employee'].search([('job_id', '=', self.job_id.id)])
                no_of_rec = len(hr_emp_obj) + no_of_recruitment
                self.write({'expected_employees': no_of_rec})
        return res

    @api.onchange('department_id')
    def onchange_department(self):
        """
            This function is used to set job ID and hof ID based on Department ID
        """
        res = {'domain': {}}
        self.job_id = False
        res['domain'].update({'job_id': [('id', 'in', [])]})
        if self.department_id:
            department = self.department_id
            job_ids = self.env['hr.job'].search([('department_id', '=', department.id)])
            self.company_id = department.company_id.id
            self.hof_id = department.manager_id.id
            self.job_id = False
            res['domain'].update({'job_id': [('id', 'in', job_ids.ids)]})
        return res

    @api.onchange('job_id')
    def onchange_job(self):
        """
            this function is used to set company ID, Department ID and Description based on job ID
        """
        self.company_id = False
        self.department_id = False
        if self.job_id:
            self.job_id.no_of_hired_employee = 0
            self.job_id.no_of_recruitment = 0
            self.company_id = self.job_id.company_id.id
            self.department_id = self.job_id.department_id.id
            self.description = self.job_id.description or ''

    @api.multi
    def requisition_confirm(self):
        """
            sent the status of generating job requisition his/her in confirm state
        """
        self.ensure_one()
        self.write({'state': 'confirm', 'approved_by_recruiter': self.env.uid, 'approved_recruiter_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion Confirmed.'))

    @api.multi
    def requisition_first_approval(self):
        """
            sent the status of generating job requisition his/her in approved1 state
        """
        self.ensure_one()
        self.write({'state': 'approved1', 'approved_by_hof': self.env.uid, 'approved_hof_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion approved.'))
        if self.is_account_manager == False:
            self.requisition_second_approval()

    @api.multi
    def requisition_second_approval(self):
        """
            sent the status of generating job requisition his/her in approved2 state
        """
        self.ensure_one()
        self.write({'state': 'approved2', 'approved_by_hop': self.env.uid, 'approved_hop_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion approved.'))

    @api.multi
    def requisition_rejected(self):
        """
            sent the status of generating job requisition his/her in rejected state
        """
        self.ensure_one()
        self.write({'state': 'rejected', 'rejected_by': self.env.uid, 'rejected_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion Reject.'))

    @api.multi
    def requisition_launch(self):
        """
            sent the status of generating job requisition his/her in approved1 launch state
        """
        self.ensure_one()
        for record in self:
            if record.approved_by_recruiter.id and record.approved_by_hof.id and record.approved_by_hop.id:
                self.message_subscribe_users(user_ids=[record.approved_by_recruiter.id, record.approved_by_hof.id, record.approved_by_hop.id])
        self.write({'state': 'launch'})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion Launch.'))

    @api.multi
    def requisition_hold(self):
        """
            sent the status of generating job requisition his/her in hold state
        """
        self.ensure_one()
        self.state = 'hold'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion Hold.'))

    @api.multi
    def requisition_done(self):
        """
            sent the status of generating job requisition his/her in done state
        """
        self.ensure_one()
        self.state = 'done'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion Done'))

    @api.multi
    def set_to_draft(self):
        """
            sent the status of generating job requisition his/her in draft state
        """
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Job Requistion Set to Draft'))
