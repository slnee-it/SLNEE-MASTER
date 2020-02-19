# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time


class OtherHrPayslip(models.Model):
    _name = 'other.hr.payslip'
    _inherit = ['mail.thread']
    _description = "Other HR Payslip"

    name = fields.Char(related='employee_id.name')
    amount = fields.Float('Amount')
    no_of_days = fields.Float('No of Days')
    operation_type = fields.Selection([('allowance', 'Allowance'),
                              ('deduction', 'Deduction')], string='Type', default='allowance', required=True)
    calc_type = fields.Selection([('amount', 'By Amount'), ('days', 'By Days'), ('hours', 'By Hours'), ('percentage', 'By Percentage')], string='Calculation Type',
                                 required=True, default='amount')
    country_id = fields.Many2one('res.country', 'Country')
    no_of_hours = fields.Float(string='No of Hours')
    percentage = fields.Float(string='Percentage')
    date = fields.Date('Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    description = fields.Text('Description', required=True)
    approved_date_to = fields.Date('Approved Date To', copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    payslip_id = fields.Many2one('hr.payslip', readonly=True, string='Payslip', copy=False)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], string='State', default='draft', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'done' states
        """
        for line in self:
            if line.state in ['done']:
                raise UserError(_('You cannot remove the record which is in %s state!') %(line.state))
        return super(OtherHrPayslip, self).unlink()

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on selected employee
            department and company
        """
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id})
        return super(OtherHrPayslip,self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id})
        return super(OtherHrPayslip, self).write(values)

    @api.multi
    def other_hr_payslip_done(self):
        """
            sent the status of other allowance/deduction request in Done state
        """
        for rec in self:
            rec.state = 'done'

    @api.multi
    def set_draft(self):
        """
            sent the status of other allowance/deduction request in Set to Draft state
        """
        for rec in self:
            rec.state = 'draft'
