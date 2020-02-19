# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import time
from datetime import datetime
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class EmployeeBonus(models.Model):
    _name = "employee.bonus"
    _description = "Employee Bonus"
    _rec_name = "employee_id"

    employee_id = fields.Many2one('hr.employee', string='Employee')
    country_id = fields.Many2one('res.country', string='Nationality', readonly=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', readonly=True)
    date_of_join = fields.Date(string='Joining Date', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    branch_id = fields.Many2one('hr.branch', 'Office', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    no_of_months = fields.Float(string='Number of Months', help="Total number of months")
    employee_bonus_ids = fields.One2many('employee.bonus.lines', 'employee_bonus_id', ondelete='cascade')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
            onchange the value based on selected employee,
            country, gender, joining date, job, department
        """
        self.country_id = False
        self.gender = False
        self.date_of_join = False
        self.job_id = False
        self.department_id = False
        self.branch_id = False
        if self.employee_id:
            self.country_id = self.employee_id.country_id.id
            self.gender = self.employee_id.gender
            self.date_of_join = self.employee_id.date_of_join
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.branch_id = self.employee_id.branch_id.id

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'country_id': employee.country_id.id,
                         'gender': employee.gender,
                         'date_of_join': employee.date_of_join,
                         'job_id': employee.job_id.id,
                         'department_id': employee.department_id.id,
                         'branch_id': employee.branch_id.id,
            })
        return super(EmployeeBonus, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values.get('employee_id'))
            values.update({'country_id': employee.country_id.id,
                           'gender': employee.gender,
                           'date_of_join': employee.date_of_join,
                           'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id,
                           'branch_id': employee.branch_id.id,
                         })
        return super(EmployeeBonus, self).write(values)

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'done' state
        """
        for rec in self:
            for line in rec.employee_bonus_ids:
                if line.state == 'done':
                    raise UserError(_('You can not delete the record for which process is already done!'))
        return super(EmployeeBonus, self).unlink()


class EmployeeBonusLines(models.Model):
    _name = "employee.bonus.lines"
    _inherit = ['mail.thread']
    _rec_name = "employee_id"
    _description = "Employee Bonus Lines"

    @api.model
    def default_get(self, fields):
        """
            Default Get From Bonus line.
        """
        data = super(EmployeeBonusLines, self).default_get(fields)
        if self._context.get('employee_id', False):
            employee_id = self.env['hr.employee'].browse(self._context.get('employee_id'))
            data.update({'employee_id': employee_id.id,
                'job_id': self._context.get('job_id', False)})
            fiscal_year = data.get('fiscalyear_id') and self.env['year.year'].browse(data.get('fiscalyear_id'))
            if fiscal_year:
                contract_ids = self.env['hr.payslip'].get_contract(employee_id, fiscal_year.date_start, fiscal_year.date_stop)
                if contract_ids:
                    wage_amt = contract_ids and self.env['hr.contract'].browse(contract_ids[0]).wage
                    data.update({
                        'wage': wage_amt,
                        'contract_id': contract_ids and contract_ids[0],
                    })
        return data

    @api.depends('bonus')
    def _get_bonus_amount(self):
        """
            Check the values of bonus if bonus > 0, increase is true or false
        """
        if self.bonus > 0:
            self.is_increase = True
        else:
            self.is_increase = False

    employee_id = fields.Many2one('hr.employee', string='Employee')
    fiscalyear_id = fields.Many2one('year.year', string='Fiscal Year', required=True, default=lambda self: self.env['year.year'].find(time.strftime("%Y-%m-%d"), True))
    period_ids = fields.Many2many('year.period', 'rel_employee_bonus_period', 'bonus_line_id', 'period_id', string='Month(s)',
                                 help='Specify month(s) in which the bonus will be distributed. Bonus will be distributed in Bonus Amount/Number of Month(s).')
    wage = fields.Float(string='Wage', digits=(16, 2), help="Basic salary of the employee", required=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=False, required=True)
    new_job_id = fields.Many2one('hr.job', string='New Job Position', required=True)
    effective_date = fields.Date(string='Effective Date', required=True)
    proposed_hike = fields.Float(string='Proposed Hike(%)', digits=(16, 2), required=True, help="Proposed hike on basic salary of the employee")
    proposed_amount = fields.Float(string='Proposed Amount', digits=(16, 2), readonly=True, help="Proposed amount on basic salary of the employee")
    accepted_hike = fields.Float(string='Accepted Hike(%)', digits=(16, 2), help="Accepted hike on basic salary of the employee")
    accepted_amount = fields.Float(string='Accepted Amount', digits=(16, 2), readonly=True, help="Accepted amount on basic salary of the employee")
    bonus = fields.Float(string='Bonus', digits=(16, 2), required=True, help="Bonus to the employee")
    bonus_percentage = fields.Float(string='Bonus(%)', digits=(16, 2), readonly=True, help="Bonus(%) to the employee")
    employee_bonus_id = fields.Many2one('employee.bonus', string='Employee Bonus', ondelete="cascade", default=lambda self: self.env.context.get('employee_bonus_id', False))
    tcc = fields.Float(string='TCC', digits=(16, 2), help="TCC(Total Cash Compensation) of the employee")
    dialogue = fields.Char(string='Dialogue')
    my_pd = fields.Selection([('1 - Outstanding Performance', '1 - Outstanding Performance'),
                              ('2 - Highly Effective Performance', '2 - Highly Effective Performance'),
                              ('3 - Effective Performance', '3 - Effective Performance'),
                              ('4 - Inconsistent Performance', '4 - Inconsistent Performance')], string='Performance Development')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Waiting for Approval'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done')], string='Status', readonly=True, default='draft',
                               help="Gives the status of Employee Bonus.", track_visibility='onchange')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    is_increase = fields.Boolean(compute=_get_bonus_amount, string='Is Increase')
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True)

    @api.onchange('proposed_hike', 'wage')
    def onchange_proposed_hike(self):
        """
            onchange the value based on selected proposed hike,
            proposed amount
        """
        if self.wage > 0 and self.proposed_hike > 0:
            proposed_amount = self.wage + (self.wage * self.proposed_hike) / 100
            self.proposed_amount = proposed_amount

    @api.onchange('accepted_hike', 'wage')
    def onchange_accepted_hike(self):
        """
            onchange the value based on selected accepted hike,
            accepted amount
        """
        if self.wage > 0 and self.accepted_hike:
            accepted_amount = self.wage + (self.wage * self.accepted_hike) / 100
            self.accepted_amount = accepted_amount

    @api.onchange('bonus')
    def onchange_bonus(self):
        """
            onchange the value based on selected bonus,
            bonus percentage
        """
        if self.wage > 0:
            bonus_perc = (self.bonus * 100) / self.wage
            self.bonus_percentage = bonus_perc

    #===========================================================================
    # @api.onchange('fiscalyear_id')
    # def onchange_fiscalyear(self):
    #     '''
    #         calculate the wage and contract duration depends on fiscal year
    #     '''
    #     if self.employee_id and self.fiscalyear_id:
    #         contract_ids = self.env['hr.payslip'].get_contract(self.employee_id, self.fiscalyear_id.date_start, self.fiscalyear_id.date_stop)
    #         if contract_ids:
    #             wage_amt = contract_ids and self.env['hr.contract'].browse(contract_ids[0]).wage
    #             self.wage = wage_amt
    #             self.contract_id = contract_ids and contract_ids[0]
    #         else:
    #             self.wage = 0.0
    #             self.contract_id = False
    #===========================================================================

    @api.onchange('employee_id', 'fiscalyear_id')
    def onchange_employee_id(self):
        """
            onchange the value based on selected employee, fiscalyear,
            wage, contract
        """
        self.wage = 0.0
        self.contract_id = False
        if self.employee_id:
            contract_ids = self.env['hr.payslip'].get_contract(self.employee_id, self.fiscalyear_id.date_start, self.fiscalyear_id.date_stop)
            if contract_ids:
                self.contract_id = contract_ids[0]
                self.wage = self.contract_id.wage

    @api.onchange('contract_id')
    def onchange_contract(self):
        """
            onchange the value based on selected contract,
            job, new job and wage
        """
        self.wage = 0.0
        if self.contract_id:
            self.wage = self.contract_id.wage

    @api.multi
    def action_button_confirm(self):
        """
            sent the status of generating record his/her bonus in 'confirm' state
        """
        self.ensure_one()
        warnings = self.env['issue.warning'].search([('id', 'in', self.employee_id.issue_warning_ids.ids), ('warning_action', '=', 'prohibit'), ('state', '=', 'done')])
        for warning in warnings:
            if self.effective_date >= warning.start_date and self.effective_date <= warning.end_date:
                raise UserError(_("You can't Confirm Bonus Line because %s have Prohibit Benefit Upgrades Warning.") % self.employee_id.name)
        self.state = 'confirm'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Bonus Confirmed.'))

    @api.multi
    def set_to_draft(self):
        """
            sent the status of generating record his/her bonus in 'draft' state
        """
        self.ensure_one()
        self.approved_by = False
        self.approved_date = False
        self.state = 'draft'

    @api.multi
    def action_button_approve(self):
        """
            sent the status of generating record his/her bonus in 'approve' state
        """
        self.ensure_one()
        self.write({'state': 'approve', 'approved_by': self.env.uid, 'approved_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Bonus Approved.'))

    @api.multi
    def action_button_cancel(self):
        """
            sent the status of generating record his/her bonus in 'cancel' state
        """
        self.ensure_one()
        self.state = 'cancel'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Bonus Cancelled.'))

    @api.multi
    def action_button_done(self):
        """
            sent the status of generating record his/her bonus in 'done' state
        """
        self.ensure_one()
        res = {}
        contract_dict = {}

        if self.contract_id:
            res = {'job_id': self.new_job_id.id}
            if self.new_job_id != self.job_id:
                self.employee_id.write(res)
                self.employee_bonus_id.write(res)
            if self.accepted_amount != 0.0:
                res.update({'wage': self.accepted_amount})
            elif self.proposed_amount != 0.0:
                res.update({'wage': self.proposed_amount})
            contract_dict.update({'wage': res.get('wage', False), 'job_id': res.get('job_id', False)})
            self.contract_id.write(contract_dict)
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Bonus Done.'))
        self.state = 'done'

    @api.multi
    def send_mail(self):
        """
            sent an email for salary promotion
        """
        self.ensure_one()
        context = self.env.context
        for line in self:
            if line.is_increase == True:
                try:
                    template_id = self.env.ref('slnee_hr_bonus.email_template_salary_promotion')
                except ValueError:
                    template_id = False
            else:
                try:
                    template_id = self.env.ref('slnee_hr_bonus.email_template_salary_no_promotion')
                except ValueError:
                    template_id = False
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({
            'default_model': 'employee.bonus.lines',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if values.get('employee_id', False) and values.get('fiscalyear_id', False):
            emp = self.env['hr.employee'].browse(values.get('employee_id'))
            fiscalyear_id = self.env['year.year'].browse(values.get('fiscalyear_id'))
            contract_ids = self.env['hr.payslip'].get_contract(emp, fiscalyear_id.date_start, fiscalyear_id.date_stop)
            if contract_ids:
                wage_amt = contract_ids and self.env['hr.contract'].browse(contract_ids[0]).wage
                values.update({'wage': wage_amt, 'contract_id': contract_ids and contract_ids[0]})
        if values.get('wage', False) and values.get('wage', False) > 0:
            wage = values.get('wage')
            if values.get('proposed_hike', False):
                proposed_amount = (wage + (wage * values.get('proposed_hike')) / 100)
                values.update({'proposed_amount': proposed_amount})
            if values.get('accepted_hike', False):
                accepted_amount = (wage + (wage * values.get('accepted_hike')) / 100)
                values.update({'accepted_amount': accepted_amount})
            if values.get('bonus', False):
                bonus_perc = ((values.get('bonus', False) * 100) / wage)
                values.update({'bonus_percentage': bonus_perc})
        return super(EmployeeBonusLines, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if values.get('employee_id', False) and values.get('fiscalyear_id', False):
            emp = self.env['hr.employee'].browse(values.get('employee_id'))
            fiscalyear_id = self.env['year.year'].browse(values.get('fiscalyear_id'))
            contract_ids = self.env['hr.payslip'].get_contract(emp, fiscalyear_id.date_start, fiscalyear_id.date_stop)
            if contract_ids:
                wage_amt = contract_ids and self.env['hr.contract'].browse(contract_ids[0]).wage
                values.update({'wage': wage_amt, 'contract_id': contract_ids and contract_ids[0]})
        if values.get('wage', False) and values.get('wage', False) > 0:
            wage = values.get('wage')
            if values.get('proposed_hike', False):
                proposed_amount = (wage + (wage * values.get('proposed_hike')) / 100)
                values.update({'proposed_amount': proposed_amount})
            if values.get('accepted_hike', False):
                accepted_amount = (wage + (wage * values.get('accepted_hike')) / 100)
                values.update({'accepted_amount': accepted_amount})
            if values.get('bonus', False):
                bonus_perc = ((values.get('bonus', False) * 100) / wage)
                values.update({'bonus_percentage': bonus_perc})
        return super(EmployeeBonusLines, self).write(values)

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'done' states
        """
        for line in self:
            if line.state in ['done']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (line.state))
        return super(EmployeeBonusLines, self).unlink()
