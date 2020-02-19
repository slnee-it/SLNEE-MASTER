# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.multi
    def _get_payment_days(self):
        for line in self:
            day_from = datetime.strptime(line.date_from, DEFAULT_SERVER_DATE_FORMAT)
            day_to = datetime.strptime(line.date_to, DEFAULT_SERVER_DATE_FORMAT)
            nb_of_days = (day_to - day_from).days + 1
            # We will set it to 30 as our calculation is based on 30 days for your company
            month = datetime.strptime(line.date_from, DEFAULT_SERVER_DATE_FORMAT).month
            if nb_of_days>30 or month==2 and nb_of_days==28: #If month is February or days are greater than 28 then payment days set to 30
                nb_of_days = 30
            line.payment_days = nb_of_days

    payment_days = fields.Float(compute='_get_payment_days', string='Payment Day(s)')

    def get_other_allowance_deduction(self, employee_id, date_from, date_to):
        from_date = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        to_date = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
        new_from_date = from_date + relativedelta(months=-1, day=25)
        last_day = calendar.monthrange(to_date.year, to_date.month)[1]
        new_to_date = to_date + relativedelta(day=24)
        if to_date.day < last_day:
            new_to_date = to_date
        domain = [('employee_id', '=', employee_id.id),
                  ('payslip_id', '=', False), ('state', 'in', ['done']),
                  ('date', '>=', new_from_date), ('date', '<=', new_to_date)]
        other_ids = self.env['other.hr.payslip'].search(domain)
        return other_ids

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        alw_no_of_days = alw_no_of_hours = alw_percentage = alw_amt = 0.0
        ded_no_of_days = ded_no_of_hours = ded_percentage = ded_amt = 0.0
        for contract in contract_ids:
            other_ids = self.get_other_allowance_deduction(contract.employee_id, date_from, date_to)
            input_deduction_lines = {}
            input_allowance_lines = {}
            if other_ids:
                for other in other_ids:
                    if other.operation_type == 'allowance':
                        if other.calc_type == 'amount':
                            alw_amt += other.amount
                            if 'OTHER_ALLOWANCE_AMOUNT' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_AMOUNT'] = alw_amt
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_AMOUNT': alw_amt})
                        elif other.calc_type == 'days':
                            alw_no_of_days += other.no_of_days
                            if 'OTHER_ALLOWANCE_DAYS' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_DAYS'] = alw_no_of_days
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_DAYS': alw_no_of_days})
                        elif other.calc_type == 'hours':
                            alw_no_of_hours += other.no_of_hours
                            if 'OTHER_ALLOWANCE_HOURS' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_HOURS'] = alw_no_of_hours
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_HOURS': alw_no_of_hours})
                        elif other.calc_type == 'percentage':
                            alw_percentage += other.percentage
                            if 'OTHER_ALLOWANCE_PERCENTAGE' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_PERCENTAGE'] = alw_percentage
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_PERCENTAGE': alw_percentage})


                    elif other.operation_type == 'deduction':
                        name = 'Other Deduction'
                        if other.calc_type == 'amount':
                            ded_amt += other.amount
                            if 'OTHER_DEDUCTION_AMOUNT' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_AMOUNT'] = ded_amt
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_AMOUNT': ded_amt})
                        elif other.calc_type == 'days':
                            ded_no_of_days += other.no_of_days
                            if 'OTHER_DEDUCTION_DAYS' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_DAYS'] = ded_no_of_days
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_DAYS': ded_no_of_days})
                        elif other.calc_type == 'hours':
                            ded_no_of_hours += other.no_of_hours
                            if 'OTHER_DEDUCTION_HOURS' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_HOURS'] = ded_no_of_hours
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_HOURS': ded_no_of_hours})
                        elif other.calc_type == 'percentage':
                            ded_percentage += other.percentage
                            if 'OTHER_DEDUCTION_PERCENTAGE' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_PERCENTAGE'] = ded_percentage
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_PERCENTAGE': ded_percentage})

                for code, amount in input_allowance_lines.items() :
                    res.append({
                                'name': 'Other Allowance',
                                'code': code,
                                'amount': amount,
                                'contract_id': contract.id,
                            })

                for code, amount in input_deduction_lines.items() :
                    res.append({
                                'name': 'Other Deduction',
                                'code': code,
                                'amount': amount,
                                'contract_id': contract.id,
                            })

        return res
