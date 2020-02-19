# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        bonus_obj = self.env['employee.bonus.lines']
        for contract in self.env['hr.contract'].browse(contracts.id):
            bonus_ids = bonus_obj.search([('employee_id', '=', contract.employee_id.id), ('state', 'in', ['done'])])
            for bonus in bonus_ids:
                bonus_amount = bonus.bonus
                if len(bonus.period_ids) > 0:
                    bonus_amount = bonus.bonus / len(bonus.period_ids)
                for period in bonus.period_ids:
                    if period.date_start == self.date_from or period.date_stop == self.date_to:
                        res.append({
                            'name': 'Employee Bonus in Fixed Amount',
                            'code': 'BONUS',
                            'amount': bonus_amount,
                            'contract_id': contract.id
                        })
        return res
