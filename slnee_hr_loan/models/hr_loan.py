# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = "Employee Loan"
    _inherit = ['mail.thread']

    @api.multi
    @api.depends('loan_amount', 'installment_lines', 'installment_lines.amount')
    def _calculate_amounts(self):
        for rec in self:
            paid_amount = 0.0
            for installment in rec.installment_lines:
                paid_amount += installment.amount
            rec.amount_paid = paid_amount
            rec.amount_to_pay = rec.loan_amount - paid_amount

    @api.multi
    @api.depends('start_date', 'duration')
    def _calculate_due_date(self):
        for rec in self:
            rec.due_date = False
            if rec.start_date:
                rec.due_date = fields.Datetime.from_string(rec.start_date) + timedelta(rec.duration * 365 / 12)

    name = fields.Char('Name', size=64, required=True)
    request_date = fields.Date('Loan Request Date', required=True, default=fields.Date.today)
    start_date = fields.Date('Loan Payment Start Date', track_visibility='onchange')
    due_date = fields.Date('Loan Payment End Date', track_visibility='onchange', compute='_calculate_due_date', store=True)
    loan_amount = fields.Float('Loan Amount', digits=dp.get_precision('Account'), required=True, track_visibility='onchange')
    duration = fields.Integer('Payment Duration(Months)', track_visibility='onchange', copy=False)
    deduction_amount = fields.Float('Deduction Amount', digits=dp.get_precision('Account'), copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    loan_type = fields.Selection([('salary', 'Loan Against Salary'),('service', 'Loan Against Service')], string="Loan Type", required=True, default='salary')
    description = fields.Text('Purpose For Loan', required=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('open', 'Waiting Approval'),
                              ('refuse', 'Refused'),
                              ('approve', 'Approved'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], string="Status", required=True, default='draft', track_visibility='onchange')
    emi_based_on = fields.Selection([('duration', 'By Duration'), ('amount', 'By Amount')], string='EMI based on',
                                    required=True, default='duration', track_visibility='onchange')
    percentage_of_gross = fields.Float('Percentage of Gross', digits=dp.get_precision('Account'))
    installment_lines = fields.One2many('installment.line', 'loan_id','Installments')
    amount_paid = fields.Float('Amount Paid', compute='_calculate_amounts', digits=dp.get_precision('Account'),
                               track_visibility='onchange')
    amount_to_pay = fields.Float('Amount to Pay', compute='_calculate_amounts', digits=dp.get_precision('Account'),
                                 track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
                                 default=lambda self: self.env.user.company_id)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    refused_by = fields.Many2one('res.users', 'Refused by', readonly=True, copy=False)
    approved_date = fields.Datetime(string='Approved on', readonly=True, copy=False)
    refused_date = fields.Datetime(string='Refused on', readonly=True, copy=False)

    @api.model
    def create(self, values):
        res = super(HrLoan, self).create(values)
        partner = []
        partner.append(self.env.user.partner_id.id)
        if res.employee_id:
            if res.employee_id.parent_id.user_id:
                partner.append(res.employee_id.parent_id.user_id.partner_id.id)
            if res.employee_id.user_id:
                partner.append(res.employee_id.user_id.partner_id.id)
        channel_id = self.env.ref('slnee_hr.manager_channel').id
        res.message_subscribe(partner_ids=partner, channel_ids=[channel_id])
        return res

    @api.multi
    def write(self, values):
        partner = []
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values.get('employee_id'))
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
            if employee.parent_id.user_id:
                partner.append(employee.parent_id.user_id.partner_id.id)
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(HrLoan, self).write(values)

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on selected employee
            department, job and company
        """
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id

    @api.multi
    def make_calculation(self):
        """
            check the loan amount, loan interest, payment duration and based on it calculate deduction amount
        """
        if not self.loan_amount or self.loan_amount < 0:
            raise UserError(_("Please enter proper value for Loan Amount & Loan Interest"))
        if self.emi_based_on == 'duration':
            if not self.duration or self.duration < 0:
                raise UserError(_("Please enter proper value for Payment Duration"))
            self.deduction_amount = self.loan_amount / self.duration
        elif self.emi_based_on == 'amount':
            if not self.deduction_amount or self.deduction_amount < 0:
                raise UserError(_("Please enter proper value for Deduction Amount"))
            count = 0
            loan_amount = self.loan_amount
            while loan_amount > 0:
                loan_amount = loan_amount - self.deduction_amount
                count += 1
            self.duration = count

    @api.multi
    def confirm_loan(self):
        """
            sent the status of generating his/her loan in Confirm state
        """
        self.ensure_one()
        self.make_calculation()
        self.due_date = fields.Datetime.from_string(self.start_date) + timedelta(self.duration * 365 / 12)
        self.state = 'confirm'

    @api.multi
    def waiting_approval_loan(self):
        """
            sent the status of generating his/her loan in Open state
        """
        self.ensure_one()
        self.due_date = fields.Datetime.from_string(self.start_date) + timedelta(self.duration * 365 / 12)
        self.state = 'open'

    @api.multi
    def approve_loan(self):
        """
            sent the status of generating his/her loan in Approve state
        """
        self.ensure_one()
        self.due_date = fields.Datetime.from_string(self.start_date) + timedelta(self.duration * 365 / 12)
        self.approved_by = self.env.uid
        self.approved_date = fields.Date.today()
        self.state = 'approve'

    @api.one
    def done_loan(self):
        """
            sent the status of generating his/her loan in Done state
        """
        self.ensure_one()
        self.state = 'done'

    @api.multi
    def refuse_loan(self):
        """
            sent the status of generating his/her loan in Refuse state
        """
        self.ensure_one()
        if self.installment_lines:
            raise UserError(_('You can not refuse a loan having any installment!'))
        self.refused_by = self.env.uid
        self.refused_date = fields.Date.today()
        self.state = 'refuse'

    @api.multi
    def set_to_draft(self):
        """
            sent the status of generating his/her loan in Set to Draft state
        """
        self.ensure_one()
        self.approved_by = False
        self.approved_date = False
        self.refused_by = False
        self.refused_date = False
        self.state = 'draft'

    @api.multi
    def set_to_cancel(self):
        """
            sent the status of generating his/her loan in Cancel state
        """
        self.ensure_one()
        self.state = 'cancel'

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'draft' and 'cancel' states
        """
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise UserError(_('You cannot delete a loan which is in %s state.') % rec.state)
            return super(HrLoan, self).unlink()


class InstallmentLine(models.Model):
    _name = 'installment.line'

    loan_id = fields.Many2one('hr.loan', 'Loan', required=True)
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    date = fields.Date('Date', required=True)
    amount = fields.Float('Installment Amount', digits=dp.get_precision('Account'), required=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    loan_ids = fields.One2many('hr.loan', 'employee_id', 'Loans')
