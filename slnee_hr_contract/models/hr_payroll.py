# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.depends('contract_id')
    def check_signon_deduction(self):
        slip_obj = self.env['hr.payslip']
        total_amt_deduct = 0.00
        employee_id = self.contract_id.employee_id
        date_of_leave = False
        if employee_id.date_of_leave:
            date_of_leave = datetime.strptime(employee_id.date_of_leave, DEFAULT_SERVER_DATE_FORMAT).date()
        if date_of_leave and employee_id.date_of_leave and employee_id.duration_in_months < 13 and date_of_leave < datetime.now().date():
            for slip_id in slip_obj.search([('state', '=', 'done')]):
                for slip_line_id in slip_id.line_ids:
                    if slip_line_id.code == 'SIGNON':
                        total_amt_deduct += slip_line_id.total
        return total_amt_deduct

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        for contract in contract_ids:
            if not contract.employee_id.date_of_leave and contract.signon_bonus_amount > 0:
                for period in contract.period_ids:
                    if len(contract.period_ids) > 0:
                        signon_amt = contract.signon_bonus_amount / len(contract.period_ids)
                    if period.date_start == self.date_from or period.date_stop == self.date_to:
                        res.append({
                            'name': 'Sign on Bonus',
                            'code': 'SIGNON_BONUS',
                            'amount': signon_amt or 0.00,
                            'contract_id': contract.id,
                        })
            signon_amount = self.check_signon_deduction()
            if signon_amount > 0:
                res.append({
                    'name': 'SIGNON Bonus Deduction',
                    'code': 'SIGNON_DEDUCTION',
                    'amount': signon_amount,
                    'contract_id': contract.id,
                })
        return res
