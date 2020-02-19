# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class IssueWarning(models.Model):
    _name = "issue.warning"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default='New')
    warning_date = fields.Date(string='Warning Date', default=datetime.today())
    warning_types = fields.Many2many('warning.type', string='Warning Types', required=True)
    warning_action = fields.Selection([('expiry', 'Expiry Period'), ('deduct', 'Deduct from Salary or not'), ('prohibit', 'Prohibit Benefit Upgrades')], string="Warning Action", required=True)
    user_id = fields.Many2one('res.users', string='Confirmed By', required=True, default=lambda self: self.env.user)
    start_date = fields.Date(string='Start Date', default=datetime.today())
    end_date = fields.Date(string='End Date')
    is_deduction_from_salary = fields.Boolean(string='Is Deduct from Salary')
    deduct_type = fields.Selection([('amount', 'By Amount'), ('days', 'By Days'), ('hours', 'By Hours'), ('percentage', 'By Percentage')], string='Deduct type')
    description = fields.Text(string='Description', required=True)
    target_group = fields.Selection([('employee', 'One Employee'), ('department','Department Wise'), ('job', 'Job Profile'), ('all_employee', 'All Employees')], string='Target Group',default='employee')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_ids = fields.Many2many('hr.department', string='Department')
    job_ids = fields.Many2many('hr.job',string='Job Profile')
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    color = fields.Integer(string='Color')
    group_mail = fields.Boolean(string='Group Mail')
    no_of_days = fields.Float(string='No of Days')
    no_of_hours = fields.Float(string='No of Hours')
    percentage = fields.Float(string='Percentage')
    ded_amt = fields.Float(string='Amount')
    state = fields.Selection([('draft', 'Draft'),
                                ('confirm', 'Confirmed'),
                                ('done', 'Done'),
                                ('cancel', 'Cancelled')], string="Status", default='draft', copy=False, track_visibility='onchange')


    @api.model
    def create(self, vals):
        """
            Override method for the add followers
        """
        vals['name'] = self.env['ir.sequence'].next_by_code('warning')
        res = super(IssueWarning, self).create(vals)
        partner=[]
        partner.append(self.env.user.partner_id.id)
        if res.employee_ids:
            for emp in res.employee_ids.ids:
                employee = self.env['hr.employee'].browse(emp)
                if employee.user_id:
                    partner.append(employee.user_id.partner_id.id)
        res.message_subscribe(partner_ids=partner)
        return res

    @api.multi
    def write(self, vals):
        """
            Override method for the add followers
        """
        # follow = self.env['mail.followers'].search([('partner_id', '!=', self.env.user.partner_id.id)]).unlink()
        partner=[]
        if vals.get('employee_ids'):
            for emp in vals['employee_ids'][0][2]:
                employee = self.env['hr.employee'].browse(emp)
                if employee.user_id:
                    partner.append(employee.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner)
        return super(IssueWarning, self).write(vals)

    @api.onchange('warning_action')
    def onchange_warning_action(self):
        self.is_deduction_from_salary = False
        self.warning_types = False
        self.deduct_type = False
        self.no_of_days = False
        self.no_of_hours = False
        self.ded_amt = False
        self.percentage = False
        res = {}
        if self.warning_action:
            warning_types = self.env['warning.type'].search([('warning_action', '=', self.warning_action)])
            self.warning_types = [(6, 0, warning_types.ids)]
            res['domain'] = {
            'warning_types': [('warning_action', '=', self.warning_action)],
        }
        return res

    @api.onchange('department_ids')
    def onchange_department_ids(self):
        employees = self.env['hr.employee'].search([('department_id', 'in', self.department_ids.ids)])
        self.employee_ids = [(6, 0, employees.ids)]

    @api.onchange('job_ids')
    def onchange_job_ids(self):
        employees = self.env['hr.employee'].search([('job_id', 'in', self.job_ids.ids)])
        self.employee_ids = [(6, 0, employees.ids)]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.employee_ids = [(6, 0, self.employee_id.ids)]

    @api.onchange('target_group')
    def onchange_target_group(self):
        self.employee_id = False
        self.employee_ids = False
        self.department_ids = False
        self.job_ids = False
        self.group_mail = False
        if self.target_group == 'all_employee':
            employees = self.env['hr.employee'].search([])
            self.employee_ids = [(6, 0, employees.ids)]

    @api.multi
    def mail_to(self):
        rec = []
        if self.employee_ids:
            for employee in self.employee_ids:
                if employee and employee.user_id:
                    rec.append(employee.user_id.partner_id.id)
        record = ', '.join(rec)
        return record

    @api.multi
    def action_mail_send(self):
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_warning', 'email_template_warning_confirm_partner')[1]
        except ValueError:
            template_id = False
        warning = []
        for warning_type in self.warning_types:
            warning.append(warning_type.name)
        if template_id and self.group_mail:
            template = self.env['mail.template'].browse(template_id)
            template.with_context({'warning':', '.join(warning)}).send_mail(self.id, force_send=True,raise_exception=False,email_values=None)
        elif template_id and not self.group_mail:
            template = self.env['mail.template'].browse(template_id)
            if self.employee_ids:
                for employee in self.employee_ids:
                    if employee.user_id:
                        partner_id = employee.user_id.partner_id.id
                        template.with_context({'email_to':partner_id, 'warning':', '.join(warning)}).send_mail(self.id, force_send=True,raise_exception=False,email_values=None)
        return True

    @api.multi
    def action_confirm(self):
        self.action_mail_send()
        warning_date = datetime.strptime(self.warning_date, DEFAULT_SERVER_DATE_FORMAT)
        warning_expiry_date = warning_date - timedelta(days=180)
        warning_ids = self.search([('state', '=', 'done'), ('employee_ids', 'in', self.employee_ids.ids),('warning_date', '>=', warning_expiry_date), ('warning_date', '<=', warning_date)])
        emp_branch_dict = {}
        branch_list = []
        if warning_ids:
            group_ids = self.env['hr.groups.configuration'].search([])
            hop_dict = {}
            for group in group_ids:
                empployee_ids = self.env['hr.employee'].search([('id', 'in', self.employee_ids.ids), ('branch_id', '=', group.branch_id.id), ('issue_warning_ids','in', warning_ids.ids)])
                emp_list = []
                for rec in empployee_ids:
                    emp_list.append(rec.name)
                    hop_list = []
                    for hop in group.hop_ids:
                        hop_list.append(hop.user_id.partner_id.id)
                    hop_dict.update({group.branch_id.id: hop_list})
                emp_branch_dict.update({group.branch_id.id: emp_list})
            for key,value in hop_dict.items():
                val = emp_branch_dict.get(key)
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference('hr_warning','email_template_warning_alert')[1]
                except ValueError:
                    template_id = False
                warning = []
                for warning_type in self.warning_types:
                    warning.append(warning_type.name)
                if template_id and warning and value and val:
                    template = self.env['mail.template'].browse(template_id)
                    hop_ids = str([value]).replace('[', '').replace(']', '')
                    template.with_context({'warning':', '.join(warning),'hop_id':hop_ids,'employee_ids':', '.join(val)}).send_mail(self.id, force_send=True,raise_exception=False,email_values=None)
        self.state = 'confirm'

    @api.multi
    def action_done(self):
        self.action_mail_send()
        other_payslip_obj = self.env['other.hr.payslip']
        for rec in self:
            #create other allowance
            payslip_data= {'employee_id': rec.employee_id.id,
                              'description': rec.description,
                              'calc_type': rec.deduct_type,
                              'amount': rec.ded_amt or 0,
                              'percentage': rec.percentage or 0,
                              'no_of_days': rec.no_of_days or 0,
                              'no_of_hours': rec.no_of_hours or 0,
                              'state': 'done',
                              'operation_type': 'deduction',
                    }
            if rec.target_group == 'employee' and rec.warning_action == 'deduct':
                other_payslip_obj.create(payslip_data)
            elif rec.target_group != 'employee' and rec.warning_action == 'deduct':
                for line in rec.employee_ids:
                    payslip_data= {'employee_id': line.id,
                                      'description': rec.description,
                                      'calc_type': rec.deduct_type,
                                      'amount': rec.ded_amt or 0,
                                      'percentage': rec.percentage or 0,
                                      'no_of_days': rec.no_of_days or 0,
                                      'no_of_hours': rec.no_of_hours or 0,
                                      'state': 'done',
                                      'operation_type': 'deduction',
                    }
                    other_payslip_obj.create(payslip_data)
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'


class HRJOb(models.Model):
    _inherit = "hr.job"

    color = fields.Integer(string='Color')
