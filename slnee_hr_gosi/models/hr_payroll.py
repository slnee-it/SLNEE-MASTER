# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _include_gosi(self):
        for line in self:
            date_from = datetime.strptime(line.date_from, DEFAULT_SERVER_DATE_FORMAT)
            day_to = datetime.strptime(line.date_to, DEFAULT_SERVER_DATE_FORMAT)
            day_upto = date_from + relativedelta(day=25)
            last_date = day_to + relativedelta(months=+1, day=1, days=-1)
            if day_to == last_date and date_from < day_upto:
                line.include_gosi = True

    gosi_id = fields.Many2one('employee.gosi', string='GOSI NO', readonly=True,
                              states={'draft': [('readonly', False)]})
    include_gosi = fields.Boolean(compute='_include_gosi', string='Include GOSI in Payslip')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        """
            onchange details of employee based on selecting gosi_id.
        """
        res = super(HrPayslip, self).onchange_employee()
        if self.employee_id:
            self.gosi_id = self.employee_id.gosi_ids.id
        return res

    @api.multi
    def action_payslip_done(self):
        """
            Overwrite the add gosi_id,payslip_id,employee_id,date,amount when payslip done.
        """
        res = super(HrPayslip, self).action_payslip_done()
        slip_line_obj = self.env['hr.payslip.line']
        gosi_payslip_line_obj = self.env['gosi.payslip.line']
        hadaf_payslip_line_obj = self.env['hadaf.payslip.line']
        for payslip in self.filtered(lambda gosi_payslip: gosi_payslip.gosi_id):
            gosi_slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'GOSI')])
            if gosi_slip_line_ids:
                amount = gosi_slip_line_ids.read(['total'])[0]['total']
                gosi_dict = {
                    'gosi_id': payslip.gosi_id.id,
                    'payslip_id': payslip.id,
                    'employee_id': payslip.employee_id.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'amount': amount if payslip.credit_note else abs(amount),
                }
                gosi_payslip_line_obj.create(gosi_dict)
            hadaf_slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'HADAF')])
            if hadaf_slip_line_ids:
                amount = hadaf_slip_line_ids.read(['total'])[0]['total']
                hadaf_dict = {
                    'hadaf_id': payslip.gosi_id.id,
                    'payslip_id': payslip.id,
                    'employee_id': payslip.employee_id.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'amount': abs(amount),
                }
                hadaf_payslip_line_obj.create(hadaf_dict)
        return res

    @api.multi
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        res = super(HrPayslip, self).onchange_employee_id(date_from=date_from, date_to=date_to, employee_id=employee_id, contract_id=contract_id)
        res['value'].update({'gosi_id': False})
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            res['value'].update({
                'gosi_id': employee.gosi_ids.id or False,
                'employee_id': employee.id,
            })
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
