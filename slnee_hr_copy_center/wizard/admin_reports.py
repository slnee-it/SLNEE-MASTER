# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import xlsxwriter
import base64
from io import BytesIO
from datetime import datetime
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AdminReports(models.TransientModel):
    _inherit = 'admin.reports'
    _order = 'id desc'

    report = fields.Selection(selection_add=[('copy_center', 'Copy Center')])

    def print_copy_center_report(self):
        report = self
        strat_date = datetime.strptime(report.date_from, DEFAULT_SERVER_DATE_FORMAT)
        month = strat_date.strftime('%m/%y')
        copy_center_pool = self.env['copy.center']

        filename = '%s.xlsx' % ('Copy Center of month %s' % month)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('copycenter')
        worksheet.set_column('B:F', 20)
        worksheet.freeze_panes(5, 0)
        header = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman',
                    'bg_color': '#da8c5e'})
        title_header = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})
        value_format = workbook.add_format({
                    'align': 'left',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})
        value_format_right = workbook.add_format({
                    'align': 'right',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})
        value_format_total_right = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'right',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})
        worksheet.write(0, 0, 'Report', title_header)
        worksheet.write(0, 1, 'Copy Center', value_format)
        worksheet.write(1, 0, 'Prepared on', title_header)
        worksheet.write(1, 1, str(datetime.now().date()), value_format)
        worksheet.write(2, 0, 'Prepared by', title_header)
        worksheet.write(2, 1, str(self.env.user.name), value_format)
        worksheet.set_column(0, 0, 18)
        worksheet.set_column(1, 1, 18)
        worksheet.set_column(2, 2, 18)
        worksheet.set_column(3, 3, 25)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 5, 30)
        worksheet.set_column(6, 6, 15)
        worksheet.set_column(7, 7, 23)
        worksheet.set_column(8, 8, 23)
        worksheet.set_column(9, 9, 15)
        worksheet.set_column(10, 10, 30)

        headers = ['Request Type', 'Employee', 'Department', 'Job Description', 'Submit Date', 'Products', 'Payment By',
                   'Employee Contribution', 'Company Contribution','Total Expense', 'Instruction']
        col = 0; row = 4
        all_col_dict = {}
        for name in headers:
            worksheet.write(row, col, name, header)
            all_col_dict.update({name: col})
            col += 1

        copy_dict = {}
        domain = [('state', '=', 'done')]
        if report.date_from:
            domain.append(('date_submited', '>=', report.date_from))
        if report.date_to:
            domain.append(('date_submited', '<=', report.date_to))
        for copy in copy_center_pool.search(domain):
            copy_dict.update({copy.id: copy_dict.get(copy.id, {})})
            line_dict = {'Request Type': copy.request_type or '',
                         'Employee': copy.employee_id.name or '',
                         'Department': copy.department_id.name or '',
                         'Job Description': copy.job_description or '',
                         'Submit Date': copy.date_submited or '',
                         'Products': ', '.join([line.product_id.name for line in copy.product_ids]) or '',
                         'Payment By': copy.payment_mode or '',
                         'Employee Contribution': copy.emp_contribution or '0.0',
                         'Company Contribution': copy.company_contribution or '0.0',
                         'Total Expense': copy.expense_total or '0.0',
                         'Instruction': copy.special_instructions or '',
                         }
            copy_dict.update({copy.id: line_dict})

        actual_data_row = row
        emp_contribution_list = []
        cmp_contribution_list = []
        total_expense_list = []
        for plan_dict in copy_dict.items():
            actual_data_row += 1
            for plan_key in plan_dict[1].keys():
                format = value_format
                if plan_key in ['Total Expense', 'Employee Contribution', 'Company Contribution']:
                    format = value_format_right
                if plan_key == 'Employee Contribution':
                    emp_contribution_list.append(float(plan_dict[1][plan_key]))
                if plan_key == 'Company Contribution':
                    cmp_contribution_list.append(float(plan_dict[1][plan_key]))
                if plan_key == 'Total Expense':
                    total_expense_list.append(float(plan_dict[1][plan_key]))
                worksheet.write(actual_data_row, all_col_dict.get(plan_key), plan_dict[1][plan_key], format)
        worksheet.write(actual_data_row+1, 7, str(sum(emp_contribution_list)) if emp_contribution_list else '0.0', value_format_total_right)
        worksheet.write(actual_data_row+1, 8, str(sum(cmp_contribution_list)) if cmp_contribution_list else '0.0', value_format_total_right)
        worksheet.write(actual_data_row+1, 9, str(sum(total_expense_list)) if total_expense_list else '0.0', value_format_total_right)
        workbook.close()
        report.write({'excel_file': base64.encodestring(fp.getvalue()), 'filename': filename})
        fp.close()

        return self.return_wiz_action(report.id)
