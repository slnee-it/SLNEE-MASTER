# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from io import BytesIO
import base64
from odoo import fields, models, api
import xlsxwriter


class CompanyPayslipReport(models.TransientModel):
    _name = "company.payslip.report"
    _description = "Company Payslip Report"

    payslip_export_id = fields.Many2one('hr.payslip.export', 'Export Structure', required=True)
    report_name = fields.Char('Report Head', size=40, required=True)
    filename = fields.Char('File Name', size=64)
    excel_file = fields.Binary('Excel File')

    @api.multi
    def print_payslip_report(self):
        fp = BytesIO()
        context = self.env.context or {}
        workbook = xlsxwriter.Workbook(fp)

        report_name = self.report_name
        filename = "%s.xlsx" % self.report_name
        structure_id = self.payslip_export_id

        if context.get('active_model', False) and context.get('active_id', False):
            payslip_batch_obj = self.env[context['active_model']]
            payslip_batch = payslip_batch_obj.browse(context['active_id'])
            sheet_name = payslip_batch.name
            worksheet = workbook.add_worksheet(sheet_name)
            bold = workbook.add_format({'bold': 1,})
            bold.set_bg_color('#C0C0C0')
            worksheet.freeze_panes(1, 2)
            row = 0
            col = 0
            initial_headers = ['Employee Code', 'Employee Name', 'Designation', 'Department', 'Pay Days']
            rule_codes = []
            salary_rule_obj = self.env['hr.payslip.export.line']
            col1 = 0
            rule_ids = salary_rule_obj.search([('payslip_export_id', '=', structure_id.id)], order='sequence')
            for rule in rule_ids:
                rule_codes.append(rule.rule_id.code)
                initial_headers.append(rule.rule_id.code)
                col1 +=1
            initial_headers.append('Notes')
            initial_headers.append('GOSI No.')
            worksheet.set_column('A:H', 10)
            for name in initial_headers:
                worksheet.write(row, col, name, bold)
                col += 1

            for payslip in payslip_batch.slip_ids:
                row += 1
                col = 0
                worksheet.write(row, col, payslip.employee_id.code or '')
                col += 1
                worksheet.write(row, col, payslip.employee_id.name or '')
                col += 1
                worksheet.write(row, col, payslip.employee_id.job_id and payslip.employee_id.job_id.name or '')
                col += 1
                worksheet.write(row, col, payslip.employee_id.department_id and payslip.employee_id.department_id.name or '')
                col += 1
                worksheet.write(row, col, payslip.payment_days)
                col += 1
                rule_column_dict = dict(zip(rule_codes, map(lambda x: (x) + col, dict(enumerate(rule_codes)).keys())))
                for slip_rule in payslip.line_ids:
                    if slip_rule.code in rule_codes:
                        worksheet.write(row, rule_column_dict[slip_rule.code], slip_rule.total)
                col += col1
                col += 1
                worksheet.write(row, col, payslip.gosi_id and payslip.gosi_id.gosi_no or '')
                
        workbook.close()
        payslip_report_id = self.create({'payslip_export_id': structure_id.id,
                                         'report_name': report_name,
                                         'excel_file': base64.encodestring(fp.getvalue()),
                                         'filename': filename})
        fp.close()

        return {
            'string': 'Payslip Report',
            'view_mode': 'form',
            'res_id': payslip_report_id.id,
            'res_model': 'company.payslip.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }
