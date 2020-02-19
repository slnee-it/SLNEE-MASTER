# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _order = 'id desc'
    _description = "Hr Expense"

    include_salary = fields.Boolean('Include in Salary', default=False)
    slip_id = fields.Many2one('hr.payslip', 'Payslip', readonly=True)
    company_contribution = fields.Float(string='Company Contribution', digits=dp.get_precision('Account'), copy=False)
    emp_contribution = fields.Float(string='Employee Contribution', digits=dp.get_precision('Account'), copy=False)

    @api.onchange('payment_mode')
    def onchange_payment_mode(self):
        if self.payment_mode == 'company_account':
            self.include_salary = False


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    _description = "Expense Report"

    include_salary = fields.Boolean('Include in Salary', compute='_set_include_salary', store=True)
    not_inc_sal_amt = fields.Float('Not Include Salary Amount Total', compute='_compute_not_inc_sal_amt', store=True)

    @api.multi
    @api.depends('expense_line_ids', 'expense_line_ids.include_salary')
    def _set_include_salary(self):
        for rec in self:
            flag = False
            for expense in rec.expense_line_ids:
                if not expense.include_salary:
                    flag = True
            if flag:
                rec.include_salary = False
            else:
                rec.include_salary = True

    @api.one
    @api.depends('expense_line_ids', 'expense_line_ids.total_amount', 'expense_line_ids.currency_id', 'expense_line_ids.include_salary')
    def _compute_not_inc_sal_amt(self):
        total_amount = 0.0
        for expense in self.expense_line_ids.filtered(lambda expense: not expense.include_salary):
            total_amount += expense.currency_id.with_context(
                date=expense.date,
                company_id=expense.company_id.id
            ).compute(expense.total_amount, self.currency_id)
        self.not_inc_sal_amt = total_amount


class HrExpensePayment(models.Model):
    _name = 'hr.expense.payment'
    _order = 'id desc'
    _description = "Hr Expense Payment"

    company_contribution = fields.Float(string='Company Contribution', digits=dp.get_precision('Account'), copy=False)
    expense_note = fields.Text(string='Expense Note', )
    emp_contribution = fields.Float(string='Employee Contribution', digits=dp.get_precision('Account'), copy=False)
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company"),
                                     ("both", "Both")], default='own_account', states={'done': [('readonly', True)],
                                    'post': [('readonly', True)]}, string="Payment By")

    @api.multi
    def generate_expense_payment(self, catch_obj, description, emp_contribution, company_contribution, payment_mode, name,
                                 product_id, expense_total):
        """
            Generate total expense of employee.
            return: created expense ID
        """
        self.ensure_one()
        expense_obj = self.env['hr.expense']
        journal = self.env['account.journal']

        if emp_contribution + company_contribution > expense_total:
            raise UserError(_('Contribution should be either greater then 0 or should not be more that total expense'))

        if not product_id:
            raise UserError(_('Please define expense products'))

        if payment_mode == 'own_account' or payment_mode == 'both':
            if emp_contribution <= 0 or emp_contribution > expense_total:
                raise UserError(_('Employee Contribution should be either greater then 0 or should not be more that total expense'))

        if payment_mode == 'company_account' or payment_mode == 'both':
            if company_contribution <= 0 or company_contribution > expense_total:
                raise UserError(_('Company Contribution should be either greater then 0 or should not be more that total expense'))

        expense_data = ({
            'employee_id': self.employee_id.id,
            'product_id': product_id.id,
            'product_uom_id': product_id.uom_id.id,
            'date': datetime.today().date(),
            'quantity': 1,
            'description': description,
            'name': name,
            'payment_mode': 'company_account',
            'unit_amount': expense_total,
            'company_contribution': company_contribution,
            'emp_contribution': emp_contribution,
        })
        if emp_contribution > 0:
            expense_data.update({'include_salary': True})
        expense_id = expense_obj.create(expense_data)
        catch_obj.expense_ids = [(4, expense_id.id)]

    @api.multi
    def redirect_to_expense(self, expense_ids):
        """
            Show employee expense.
        """
        self.ensure_one()
        tree_view = self.env.ref('hr_expense.view_expenses_tree')
        form_view = self.env.ref('hr_expense.hr_expense_form_view')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses'),
            'res_model': 'hr.expense',
            'view_type': 'form',
            'view_mode': 'from',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', 'in', expense_ids.ids)],
            'res_id': expense_ids.ids,
            'context': self.env.context,
        }
