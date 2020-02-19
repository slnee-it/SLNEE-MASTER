# -*- coding: utf-8 -*-

import time
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

max_total_payble_limit = 37500.00


class HrExpense(models.Model):
    _inherit = "hr.expense"

    @api.depends('company_contribution', 'total_amount')
    def _get_employee_contribution(self):
        """
            Calculate employee contribution for expense.
        """
        for contribute_rec in self:
            if contribute_rec.company_contribution <= contribute_rec.total_amount:
                contribute_rec.employee_contribution = contribute_rec.total_amount - contribute_rec.company_contribution

    include_salary = fields.Boolean('Include in Salary', default=True)
    job_id = fields.Many2one('hr.job', 'Job Position', readonly=True)
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    source = fields.Char('Source', size=128)
    requested_by = fields.Many2one('res.users', 'Requested By')
    visibility_reimburse = fields.Boolean('Visibility School Reimburse')
    company_contribution = fields.Float('- Company Contribution')
    employee_contribution = fields.Float('Employee Contribution', compute=_get_employee_contribution, store=True)
    refused_by = fields.Many2one('res.users', 'Refused By', copy=False)
    refused_date = fields.Datetime('Refused on', copy=False)
    slip_id = fields.Many2one('hr.payslip', 'Payslip', readonly=True)

    @api.multi
    def unlink(self):
        if self._context is None:
            self._context = {}
        for object in self:
            if object.state in ['reported', 'done', 'refused']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (object.state))
        return super(HrExpense, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('employee_id', False):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id,
                         'job_id': employee.job_id.id,
                       })
        return super(HrExpense, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            vals.update({'job_id': employee.job_id.id,
                         'department_id': employee.department_id.id})
        return super(HrExpense, self).write(vals)

    @api.multi
    @api.constrains('company_contribution')
    def _check_company_contribution(self):
        """
            Check company contribution for expense.
        """
        for obj in self:
            if obj.company_contribution and obj.company_contribution > obj.total_amount:
                raise UserError(_('Company Contribution must not greater than total amount'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
            Set name according to product.
        """
        super(HrExpense, self)._onchange_product_id()
        if self.product_id:
            self.name = self.product_id.display_name

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
            Set employee code and job according to employee.
        """
        self.job_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            if self.employee_id.grade_id and self.employee_id.grade_id.is_above_manager and self.employee_id.marital in  ['married', 'divorced', 'widower'] and self.employee_id.children > 0:
                self.visibility_reimburse = True
            else:
                self.visibility_reimburse = False

    @api.multi
    def submit_expenses(self):
        """
            Submit employee expense.
        """
        res = super(HrExpense, self).submit_expenses()
        for expense in self:
            if expense.employee_id and expense.employee_id.coach_id.user_id:
                expense.message_subscribe_users(user_ids=[expense.employee_id.coach_id.user_id.id])
            expense.date_confirm = time.strftime('%Y-%m-%d')
        return res

    @api.multi
    def refuse_expenses(self, reason):
        """
            Change state to refuse.
        """
        self.ensure_one()
        self.write({'refused_by': self.env.uid, 'refused_date': datetime.today()})
        return super(HrExpense, self).refuse_expenses(reason)

    @api.multi
    def reset_expenses(self):
        """
            Change state to draft.
        """
        self.ensure_one()
        return self.write({'state': 'draft'})

    @api.multi
    def _move_line_get(self):
        account_move = []
        for expense in self:
            if expense.company_contribution > 0:
                move_line = {
                    'type': 'src',
                    'name': expense.name.split('\n')[0][:64],
                    'price_unit': expense.unit_amount,
                    'quantity': expense.quantity,
                    'price': expense.company_contribution,
                    'account_id': expense.sheet_id.bank_journal_id.default_credit_account_id.id,
                    'product_id': expense.product_id.id,
                    'uom_id': expense.product_uom_id.id,
                    'analytic_account_id': expense.analytic_account_id.id,
                }
                account_move.append(move_line)
            if expense.product_id:
                account = expense.product_id.product_tmpl_id._get_product_accounts()['expense']
                if not account:
                    raise UserError(_("No Expense account found for the product %s (or for it's category), please configure one.") % (expense.product_id.name))
            else:
                account = self.env['ir.property'].with_context(force_company=expense.company_id.id).get('property_account_expense_categ_id', 'product.category')
                if not account:
                    raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
            move_line = {
                    'type': 'src',
                    'name': expense.name.split('\n')[0][:64],
                    'price_unit': expense.unit_amount,
                    'quantity': expense.quantity,
                    'price': expense.employee_contribution,
                    'account_id': account.id,
                    'product_id': expense.product_id.id,
                    'uom_id': expense.product_uom_id.id,
                    'analytic_account_id': expense.analytic_account_id.id,
                }
            account_move.append(move_line)

            # Calculate tax lines and adjust base line
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            account_move[-1]['price'] = taxes['total_excluded']
            account_move[-1]['tax_ids'] = expense.tax_ids.id
            for tax in taxes['taxes']:
                account_move.append({
                    'type': 'tax',
                    'name': tax['name'],
                    'price_unit': tax['amount'],
                    'quantity': 1,
                    'price': tax['amount'],
                    'account_id': tax['account_id'] or move_line['account_id'],
                    'tax_line_id': tax['id'],
                })
        return account_move


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    approved_date = fields.Datetime('Approved Date', copy=False)
    approved_by = fields.Many2one('res.users', 'Approved By', copy=False)
    date_of_approve = fields.Date('Approved Date', copy=False)

    @api.multi
    def approve_expense_sheets(self):
        """
            Change state to approve and send mail to employee.
        """
        self.ensure_one()
        today = datetime.today()
        hr_groups_config_obj = self.env['hr.groups.configuration']
        hr_groups_config_ids = hr_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id), ('finance_ids', '!=', False)])
        user_ids = hr_groups_config_ids and [item.user_id.id for item in hr_groups_config_ids.finance_ids if item.user_id] or []
        self.message_subscribe_users(user_ids=user_ids)
        self.write({'approved_by': self._uid, 'approved_date': today, 'date_of_approve':today})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Expense Validated'))
        return super(HrExpenseSheet, self).approve_expense_sheets()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
