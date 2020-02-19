# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        loan_obj = self.env['hr.loan']
        skip_installment_obj = self.env['hr.skip.installment']
        slip_line_obj = self.env['hr.payslip.line']
        installment_obj = self.env['installment.line']
        for payslip in self:
            loan_ids = loan_obj.search(['|','&',('start_date','>=',payslip.date_from),('start_date','<=',payslip.date_to),('start_date','<=',payslip.date_from),('employee_id', '=', payslip.employee_id.id), ('state', '=', 'approve')])
            for loan in loan_ids:
                skip_installment_ids = skip_installment_obj.search([('loan_id','=',loan.id),('state','=','approve'),('date','>=',payslip.date_from),('date','<=',payslip.date_to)])
                if skip_installment_ids:
                    due_date = datetime.strptime(loan.due_date, '%Y-%m-%d') + relativedelta(months=1)
                    loan.write({'due_date': due_date})
                else:
                    slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'LOAN' + str(loan.id))])
                    if slip_line_ids:
                        amount = slip_line_ids.read(['total'])[0]['total']
                        installment_data = {
                            'loan_id': loan.id,
                            'payslip_id': payslip.id,
                            'employee_id': payslip.employee_id.id,
                            'amount': amount if payslip.credit_note else abs(amount),
                            'date': time.strftime('%Y-%m-%d')
                        }
                        installment_obj.create(installment_data)
                    if loan.amount_to_pay <= 0:
                        loan.write({'state': 'done'})
        return res

    def check_installments_to_pay(self):
        slip_line_obj = self.env['hr.payslip.line']
        loan_obj = self.env['hr.loan']
        rule_obj = self.env['hr.salary.rule']
        skip_installment_obj = self.env['hr.skip.installment']
        for payslip in self:
            if not payslip.contract_id:
                raise UserError(_("Please enter Employee contract first."))
            loan_ids = loan_obj.search(['|', '&', ('start_date', '>=', payslip.date_from),
                                        ('start_date', '<=', payslip.date_to),
                                        ('start_date', '<=', payslip.date_from),
                                        ('employee_id', '=', payslip.employee_id.id),
                                        ('state', '=', 'approve')])
            rule_ids = rule_obj.search([('code', '=', 'LOAN')])
            if rule_ids:
                rule = rule_ids[0]
                oids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'LOAN')])
                if oids:
                    oids.unlink()
                for loan in loan_ids:
                    skip_installment_ids = skip_installment_obj.search([('loan_id','=',loan.id),('state','=','approve'),('date','>=',payslip.date_from),('date','<=',payslip.date_to)])
                    if not skip_installment_ids:
                        slip_line_data = {
                            'slip_id': payslip.id,
                            'salary_rule_id': rule.id,
                            'contract_id': payslip.contract_id.id,
                            'name': loan.name,
                            'code': 'LOAN' + str(loan.id),
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence + loan.id,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': -(loan.deduction_amount),
                            'employee_id': payslip.employee_id.id,
                        }
                        if abs(slip_line_data['amount']) > loan.amount_to_pay:
                            slip_line_data.update({'amount': -(loan.amount_to_pay)})
                        slip_line_obj.create(slip_line_data)
                        net_ids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'NET')])
                        if net_ids:
                            net_record = net_ids[0]
                            net_ids.write({'amount': net_record.amount + slip_line_data['amount']})
        return True

    @api.multi
    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        for payslip in self:
            payslip.check_installments_to_pay()
        return res
