# Part of odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import models, fields, api, _
from dateutil import relativedelta
from datetime import date,datetime
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HrEmployeeEos(models.Model):
    _name = 'hr.employee.eos'
    _inherit = ['mail.thread']
    _description = "End of Service Indemnity (EOS)"

    @api.multi
    def _get_currency(self):
        """
            return currency of current user
        """
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.currency_id.id

    @api.multi
    def _calc_payable_eos(self):
        """
            Calculate the payable eos
        """
        for eos_amt in self:
            eos_amt.payable_eos = (eos_amt.total_eos + eos_amt.current_month_salary + eos_amt.others + eos_amt.annual_leave_amount) or 0.0

    name = fields.Char('Description', size=128, required=True, readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    eos_date = fields.Date('Date', index=True,required=True, readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, default=lambda self: datetime.today().date())
    employee_id = fields.Many2one('hr.employee', "Employee", required=True, readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    date_of_join = fields.Date(related='employee_id.date_of_join', type="date", string="Joining Date", store=True,readonly=True)
    date_of_leave = fields.Date(related='employee_id.date_of_leave', type="date", string="Leaving Date", store=True,readonly=True)
    duration_days = fields.Integer('No of Days',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    duration_months = fields.Integer('No of Months',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    duration_years = fields.Integer('No. of Years',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    type = fields.Selection([('resignation','Resignation'),('termination','Termination'),('death','Death')],'Type',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    calc_year = fields.Float('Total Years',readonly=True,states={'draft':[('readonly',False)]})
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', readonly=True)
    current_month_salary = fields.Float('Salary of Current month',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    others = fields.Float('Others',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.uid)
    date_confirm = fields.Date('Confirmation Date', index=True, help="Date of the confirmation of the sheet expense. It's filled when the button Confirm is pressed.")
    date_valid = fields.Date('Validation Date', index=True, help="Date of the acceptation of the sheet eos. It's filled when the button Validate is pressed.")
    date_approve = fields.Date('Approve Date', index=True, help="Date of the Approval of the sheet eos. It's filled when the button Approve is pressed.")
    user_valid = fields.Many2one('res.users', 'Validation by', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]},store=True)
    user_approve = fields.Many2one('res.users', 'Approval by', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]},store=True)
    note = fields.Text('Note')
    annual_leave_amount = fields.Float('Leave Balance',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    department_id = fields.Many2one('hr.department',"Department", readonly=True)
    job_id = fields.Many2one('hr.job','Job', readonly=True)
    contract_id = fields.Many2one('hr.contract','Contract', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    company_id = fields.Many2one('res.company', 'Company', required=True,readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('draft', 'New'),
        ('cancelled', 'Refused'),
        ('confirm', 'Waiting Approval'),
        ('validate','Validated'),
        ('accepted', 'Approved'),
        ('done', 'Done'),
        ],
        'Status', readonly=True, track_visibility='onchange', default='draft',
        help='When the eos request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to finance, the status is \'Waiting Confirmation\'.\
        \nIf the finance accepts it, the status is \'Accepted\'.')
    total_eos = fields.Float('Total Award',readonly=True,states={'draft':[('readonly',False)]})
    payable_eos = fields.Float(compute=_calc_payable_eos,string='Total Amount')
    remaining_leave = fields.Float('Remaining Leave')
    # account
    journal_id = fields.Many2one('account.journal', 'Force Journal', help = "The journal used when the eos is done.")
    account_move_id = fields.Many2one('account.move', 'Ledger Posting')
    voucher_id = fields.Many2one('account.voucher', "Employee's Receipt")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, default=_get_currency)
    year_id = fields.Many2one('year.year', 'Year', required=True, readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, index=True, default=lambda self: self.env['year.year'].find(time.strftime("%Y-%m-%d"), True))

    @api.multi
    def _track_subtype(self, init_values):
        """
            Track Subtypes of EOS
        """
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'slnee_hr_eos.mt_employee_eos_new'
        elif 'state' in init_values and self.state == 'confirm':
            return 'slnee_hr_eos.mt_employee_eos_confirm'
        elif 'state' in init_values and self.state == 'accepted':
            return 'slnee_hr_eos.mt_employee_eos_accept'
        elif 'state' in init_values and self.state == 'validate':
            return 'slnee_hr_eos.mt_employee_eos_validate'
        elif 'state' in init_values and self.state == 'done':
            return 'slnee_hr_eos.mt_employee_eos_done'
        elif 'state' in init_values and self.state == 'cancelled':
            return 'slnee_hr_eos.mt_employee_eos_cancel'
        return super(HrEmployeeEos, self)._track_subtype(init_values)

    @api.multi
    def copy(self, default=None):
        """
            Duplicate record
        """
        default = dict(default or {})
        default.update(
            account_move_id=False,
            date_confirm=False,
            date_valid=False,
            date_approve=False,
            user_valid=False)
        return super(HrEmployeeEos, self).copy(default=default)

    @api.model
    def create(self, vals):
        """
            Create a new Record
        """
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'job_id': employee.job_id.id,
                         'department_id': employee.department_id.id,
                         })
        return super(HrEmployeeEos,self).create(vals)

    @api.multi
    def write(self, vals):
        """
            update existing record
        """
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'job_id': employee.job_id.id,
                         'department_id': employee.department_id.id,
                         })
        return super(HrEmployeeEos,self).write(vals)

    @api.multi
    def unlink(self):
        """
            Remove record
        """
        for object in self:
            if object.state in ['confirm','validate','accepted','done','cancelled']:
                raise UserError(_('You cannot remove the record which is in %s state!')%(object.state))
        return super(HrEmployeeEos, self).unlink()

    @api.onchange('currency_id', 'company_id')
    def onchange_currency_id(self):
        """
            find the journal using currency
        """
        journal_ids = self.env['account.journal'].search([('type','=','purchase'), ('currency_id','=',self.currency_id.id), ('company_id', '=', self.company_id.id)], limit=1)
        if journal_ids:
            self.journal_id = journal_ids[0].id

    @api.multi
    def calc_eos(self):
        """
            Calculate eos
        """
        user_id = self.env.user
        payslip_obj = self.env['hr.payslip']
        for eos in self:
            join_date = datetime.strptime(eos.date_of_join, DEFAULT_SERVER_DATE_FORMAT)
            if not eos.date_of_leave:
                raise UserError(_('Please define employee date of leaving!'))
            leave_date = datetime.strptime(eos.date_of_leave, DEFAULT_SERVER_DATE_FORMAT)
            diff = relativedelta.relativedelta(leave_date, join_date)
            duration_days = diff.days
            duration_months = diff.months
            duration_years = diff.years
            eos.write({'duration_days': duration_days, 'duration_months': duration_months, 'duration_years': duration_years})
            selected_date = datetime.strptime(eos.date_of_leave,DEFAULT_SERVER_DATE_FORMAT)
            selected_month = selected_date.month
            selected_year = selected_date.year
            date_from = date(selected_year,selected_month,1)
            l_d = date_from + relativedelta.relativedelta(day=selected_date.day)
            date_to = datetime.strftime(l_d,'%Y-%m-%d')
            contract_ids = self.payslip_id.get_contract(eos.employee_id, date_from, date_to)
            if not contract_ids:
                raise UserError(_('Please define contract for selected Employee!'))
            # Currently your company contract wage will be calculate as last salary.
            wages = self.env['hr.contract'].browse(contract_ids[0]).wage
            total_eos = 0.0
            if duration_years >= 2 and duration_years < 5:
                total_eos = ((wages / 2) * duration_years) + (((wages/2) / 12) * duration_months) + ((((wages/2) /12) /30) * duration_days)
            elif duration_years >= 5 and duration_years < 10:
                total_eos = ((wages / 2) * duration_years) + ((wages / 12) * duration_months) + (((wages /12) /30) * duration_days)
            elif duration_years >= 10:
                total_eos = ((wages / 2) * 5) + (wages * (duration_years - 5)) + ((wages / 12) * duration_months) + ((wages /365) * duration_days)
            date_from = datetime.strftime(date_from,'%Y-%m-%d')
            if not eos.contract_id.journal_id:
                raise UserError (_('Please configure employee contract for journal.'))
            vals = {
                'employee_id': eos.employee_id.id or False,
                'date_from': date_from,
                'date_to': date_to,
                'contract_id': contract_ids[0],
                'struct_id': eos.contract_id.struct_id.id or False,
                'journal_id': eos.contract_id.journal_id.id or False,
            }
            if not eos.payslip_id:
                payslip_id = payslip_obj.create(vals)
                eos.write({'payslip_id': payslip_id.id})
            onchange_result = eos.payslip_id.onchange_employee_id(date_from, date_to, eos.employee_id.id, contract_ids[0])
            vals1 = onchange_result['value']
            if vals1.get('worked_days_line_ids'):
                vals1['worked_days_line_ids'] = [[5, False, False]] + [[0, False, line] for line in vals1['worked_days_line_ids']]
            if vals1.get('input_line_ids'):
                vals1['input_line_ids'] = [[5, False, False]] + [[0, False, line] for line in vals1['input_line_ids']]
            if vals1.get('leaves_summary'):
                vals1['leaves_summary'] = [[5, False, False]] + [[0, False, line] for line in vals1['leaves_summary']]
            eos.payslip_id.write(vals1)
            eos.payslip_id.compute_sheet()
            net = 0.00
            payslip_line_obj = self.env['hr.payslip.line']
            net_rule_id = payslip_line_obj.search([('slip_id', '=', eos.payslip_id.id),('code','ilike','NET')])
            if net_rule_id:
                net_rule_obj = net_rule_id[0]
                net = net_rule_obj.total
            eos.write({'current_month_salary': net,})# 'basic_salary': basic_salary, 'hra': hra, 'ta': ta, 'other_allowance': other
            payable_eos = total_eos
            if eos.type == 'resignation':
                if eos.calc_year > 2 and eos.calc_year < 5:
                    payable_eos = total_eos / 3
                elif eos.calc_year > 2 and eos.calc_year < 10:
                    payable_eos = (total_eos * 2) / 3
                elif eos.calc_year > 10:
                    payable_eos = total_eos

            # Annual Leave Calc
            holiday_status_pool = self.env['hr.holidays.status']
            holiday_status_ids = holiday_status_pool.search([('carry_forward','=',True)])
            annual_leave_amount = 0.0
            remaining_leaves = 0.0
            if holiday_status_ids:
                leave_values = holiday_status_ids.get_days(eos.employee_id.id, eos.year_id.id)
                leaves_taken = leave_values[holiday_status_ids[0].id]['leaves_taken']
                year_start_date = datetime.strptime(eos.year_id.date_start, DEFAULT_SERVER_DATE_FORMAT)
                diff_date = relativedelta.relativedelta(leave_date, year_start_date)
                allocate_leave_month = diff_date.months * eos.job_id.annual_leave_rate
                remaining_leaves = (allocate_leave_month - leaves_taken) + leave_values[holiday_status_ids[0].id]['carry_forward_leaves']
                annual_leave_amount = (wages / 30) * remaining_leaves
                eos.write({'total_eos':payable_eos,'annual_leave_amount':annual_leave_amount,'remaining_leave': remaining_leaves})
            return True

    @api.onchange('employee_id', 'eos_date')
    def onchange_employee_id(self):
        """
            Calculate total no of year, month, days, etc depends on employee
        """
        payslip_obj = self.env['hr.payslip']
        contract_ids = False
        if self.employee_id:
            if not self.employee_id.date_of_leave:
                raise UserError(_('Please define employee date of leaving!'))
            if not self.employee_id.date_of_join:
                raise UserError(_('Please define employee date of join!'))
            selected_date = datetime.strptime(self.employee_id.date_of_leave,DEFAULT_SERVER_DATE_FORMAT)
            date_from = date(selected_date.year,selected_date.month, 1)
            l_d = date_from + relativedelta.relativedelta(day=selected_date.day)
            date_to = datetime.strftime(l_d,'%Y-%m-%d')
            contract_ids = self.payslip_id.get_contract(self.employee_id, date_from, date_to)
            if not contract_ids:
                raise UserError(_('Please define contract for selected Employee!'))
            join_date = datetime.strptime(self.employee_id.date_of_join, DEFAULT_SERVER_DATE_FORMAT)
            leave_date = datetime.strptime(self.employee_id.date_of_leave, DEFAULT_SERVER_DATE_FORMAT)
            calc_years = round(((leave_date - join_date).days / 365.0),2)
            diff = relativedelta.relativedelta(leave_date, join_date)
            self.contract_id = contract_ids[0]
            self.date_of_leave = self.employee_id.date_of_leave
            self.date_of_join = self.employee_id.date_of_join
            self.calc_year = calc_years
            self.department_id = self.employee_id.department_id.id or False
            self.company_id = self.employee_id.company_id.id or False
            self.job_id = self.employee_id.job_id.id or False
            self.duration_years = diff.years or 0
            self.duration_months = diff.months or 0
            self.duration_days = diff.days or 0

    @api.multi
    def eos_confirm(self):
        """
            EOS confirm state.
        """
        self.ensure_one()
        self.write({'state': 'confirm', 'date_confirm': time.strftime('%Y-%m-%d')})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('EOS Confirmed.'))

    @api.multi
    def eos_validate(self):
        """
            EOS validate state.
        """
        self.ensure_one()
        finance_groups_config_obj = self.env['hr.groups.configuration']
        for record in self:
            finance_groups_config_ids = finance_groups_config_obj.search([('branch_id', '=', record.employee_id.branch_id.id or False), ('finance_ids', '!=', False)])
            finance_groups_ids = finance_groups_config_ids and finance_groups_config_ids[0]
            if finance_groups_ids:
                user_ids = [item.user_id.id for item in finance_groups_ids.finance_ids if item.user_id]
                record.message_subscribe_users(user_ids)
        for eos in self:
            self.calc_eos()
            if eos.employee_id.parent_id.user_id:
                eos.message_subscribe_users(user_ids=[eos.employee_id.parent_id.user_id.id])
        self.write({'state': 'validate', 'date_valid': time.strftime('%Y-%m-%d'), 'user_valid': self.env.uid})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('EOS Validated.'))

    @api.multi
    def eos_accept(self):
        """
            EOS accept state
        """
        self.ensure_one()
        self.write({'state': 'accepted', 'date_approve': time.strftime('%Y-%m-%d'), 'user_approve': self.env.uid})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('EOS Approved.'))

    @api.multi
    def eos_canceled(self):
        """
            EOS confirm state
        """
        self.ensure_one()
        self.state = 'cancelled'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('EOS Cancelled.'))

    @api.multi
    def eos_draft(self):
        """
            EOS set to draft state
        """
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('EOS Draft.'))

    @api.multi
    def account_move_get(self):
        """
            This method prepare the creation of the account move related to the given expense.

            :param eos_id: Id of voucher for which we are creating account_move.
            :return: mapping between fieldname and value of account move to create
            :rtype: dict
        """
        self.ensure_one()
        journal_obj = self.env['account.journal']
        company_id = self.company_id.id
        date = self.date_confirm
        ref = self.name
        journal_id = False
        if self.journal_id:
            journal_id = self.journal_id.id
        else:
            journal_id = journal_obj.search([('type', '=', 'purchase'), ('company_id', '=', company_id)])
            if not journal_id:
                raise UserError(_("No EOS journal found. Please make sure you have a journal with type 'purchase' configured."))
            journal_id = journal_id[0].id
        return self.env['account.move'].account_move_prepare(journal_id, date=date, ref=ref, company_id=company_id)

    @api.multi
    def line_get_convert(self, x, part, date):
        """
            line get convert
        """
        partner_id  = self.env['res.partner']._find_accounting_partner(part).id
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': partner_id,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', False),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
        }

    @api.multi
    def action_receipt_create(self):
        """
            main function that is called when trying to create the accounting entries related to an expense
        """
        for eos in self:
            if not eos.employee_id.address_home_id:
                raise UserError(_('The employee must have a home address.'))
            if not eos.employee_id.address_home_id.property_account_payable_id.id:
                raise UserError(_('The employee must have a payable account set on his home address.'))
            company_currency = eos.company_id.currency_id.id
            diff_currency_p = eos.currency_id.id != company_currency
            eml = []
            if not eos.contract_id.journal_id:
                raise UserError (_('Please configure employee contract for journal.'))

            move_id = self.env['account.move'].create({
            'journal_id': eos.contract_id.journal_id.id,
            'company_id': eos.env.user.company_id.id,
            })

            #create the move that will contain the accounting entries
            ctx = self._context.copy()
            ctx.update({'force_company': eos.company_id.id})
            acc = self.env['ir.property'].with_context(ctx).get('property_account_expense_categ_id', 'product.category')
            if not acc:
                raise UserError(_('Please configure Default Expense account for Product purchase: `property_account_expense_categ`.'))
            acc1 = eos.employee_id.address_home_id.property_account_payable_id
            eml.append({
                'type':'src',
                'name': eos.name.split('\n')[0][:64],
                'price': eos.payable_eos,
                'account_id':acc.id,
                'date_maturity': eos.date_confirm,
               })
            total = 0.0
            total -= eos.payable_eos
            eml.append({
                    'type': 'dest',
                    'name': '/',
                    'price': total,
                    'account_id': acc1.id,
                    'date_maturity': eos.date_confirm,
                    'amount_currency': diff_currency_p and eos.currency_id.id or False,
                    'currency_id': diff_currency_p and eos.currency_id.id or False,
                    'ref': eos.name,
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x:(0,0,self.line_get_convert(x, eos.employee_id.address_home_id, eos.date_confirm)), eml)
            # journal_id = move_obj.browse(cr, uid, move_id, context).journal_id

            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            # if journal_id.entry_posted:
            #     move_obj.button_validate(cr, uid, [move_id], context)

            move_id.write({'line_ids': lines})
            self.write({'account_move_id': move_id.id, 'state': 'done'})
        return True

    @api.multi
    def action_view_receipt(self):
        """
            This function returns an action that display existing account.move of given expense ids.
        """
        assert len(self.ids) == 1, 'This option should only be used for a single id at a time'
        self.ensure_one()
        assert self.account_move_id
        try:
            dummy, view_id = self.env['ir.model.data'].get_object_reference('account', 'view_move_form')
        except ValueError:
            view_id = False
        result = {
            'name': _('EOS Account Move'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': self.account_move_id.id,
        }
        return result


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'HR Job'

    annual_leave_rate = fields.Float('Annual Leave Rate', default=2)
