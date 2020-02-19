# -*- coding: utf-8 -*-

from cStringIO import StringIO
import base64
from odoo import fields, models, api
import xlsxwriter
from odoo.tools.translate import _
from xlsxwriter.utility import xl_rowcol_to_cell
from datetime import datetime

class bonus_report(models.TransientModel):
    _name = 'bonus.report'
    _description = 'Bonus Report'

    filename = fields.Char('File Name', size=64)
    excel_file = fields.Binary('Excel File')


    @api.multi
    def get_gender(self, gender):
        if gender == 'male':
            return 'M'
        elif gender == 'female':
            return 'F'
        else:
            return ''

    @api.multi
    def print_bonus_report(self):
        branch_pool = self.env[self.env.context.get('active_model')]
        branch_id = self.env.context.get('active_id')
        branch = branch_pool.browse(branch_id)
        bonus_ids = map(lambda x:x.id, branch.employee_bonus_ids)
#         bonus_pool = self.env['employee.bonus']
#         fiscalyear_pool = self.pool.get('account.fiscalyear')
        current_year = (datetime.today()).year
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        headers = ['Employee ID', 'Employee Name', 'Nationality', 'Gender', 'DOJ', 'Designation', 'Grade', 'Function', 'Sub Function', 'Location', 'Promotion to?']
#         for future use ========= dont delete it.....
#         department_id = branch_id = False
#         if record.type == 'department' and record.department_id:
#             department_ids = department_pool.search(cr, uid, [('parent_id','=', record.department_id.id)])
#             bonus_ids = bonus_pool.search(cr, uid, [('department_id','in',department_ids)], context=context)
#             department_id = record.department_id.id
#             filename = 'Bonus Report of %s.xlsx'%(record.department_id.name)
#             worksheet = workbook.add_worksheet(record.department_id.name)
#         elif record.type == 'office' and record.branch_id:
#             bonus_ids = bonus_pool.search(cr, uid, [('branch_id','=',record.branch_id.id)], context=context)
#             branch_id = record.branch_id.id
#             filename = 'Bonus Report of %s.xlsx'%(record.branch_id.name)
#             worksheet = workbook.add_worksheet(record.branch_id.name)
#         else:
#             bonus_ids = bonus_pool.search(cr, uid, [], context=context)
#             filename = 'Bonus Report %s.xlsx'%(current_year)
#             worksheet = workbook.add_worksheet('Bonus FY %s'% current_year)
        filename = 'Bonus Report %s.xlsx' % (current_year)
        worksheet = workbook.add_worksheet(branch.department_id and branch.department_id.name or '')
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 30)
        header = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'font_name': 'Times New Roman'})
#         header.set_locked(True)
        green = workbook.add_format({
                    'align': 'left',
                    'font_size': 10,
                    'valign': 'vleft',
                    'font_name': 'Times New Roman'})
        totals = workbook.add_format({
                    'bold': 1,
                    'border': 2,
                    'bg_color':'#fcce1c',
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 10,
                    'font_name': 'Times New Roman'})
        details_center = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 10,
                    'font_name': 'Times New Roman'})
        details_format = workbook.add_format({
                    'align': 'left',
                    'font_size': 10,
                    'valign': 'vleft',
                    'font_name': 'Times New Roman'})
        unlocked_details_format = workbook.add_format({
                    'align': 'left',
                    'font_size': 10,
                    'valign': 'vleft',
                    'bg_color': '#75ad3e',
                    'font_name': 'Times New Roman'})
        # Below two lines are used for locked cells [to make readonly some columns]
        unlocked_details_format.set_locked(False)
        worksheet.protect()
        row = 0; col = 0;
        worksheet.merge_range(row, col, row, col + 1, '', header)
        worksheet.merge_range(row, col + 2, row, col + 9, 'Salary FY %s' % (current_year), header)
        worksheet.freeze_panes(0, 2)
        row += 1
        all_col_dict = {}
        for name in headers:
            worksheet.write(row, col, name, header)
            all_col_dict.update({name: col})
            col += 1

        fy = []
        bonus_dict = {}
#         dates = []
        fy.append(str(current_year))
        fy.append(str(current_year - 1))
        fy.append(str(current_year - 2))
        fy.append(str(current_year - 3))
        fy.append(str(current_year - 4))
#         for future use==================dont delete it..........
#         fiscalyear_ids = fiscalyear_pool.search(cr, uid, [('date_start','in',dates)], context=context)
#         if fiscalyear_ids:
#             for fiscalyear in fiscalyear_pool.browse(cr, uid, fiscalyear_ids, context=context):
#                 fy.append(str(datetime.strptime(fiscalyear.date_start,'%Y-%m-%d').year))
        fy.sort()

        if fy:
            for fyear in fy:
                if cmp(fyear, str(current_year)) == 0:
                    worksheet.write(row, col, 'Current \n Salary FY ' + fyear, header)
                else:
                    worksheet.write(row, col, 'Salary \n FY ' + fyear, header)
                all_col_dict.update({'Salary FY %s' % fyear: col})
                col += 1
        worksheet.write(row, col, '% Increase', header)
        all_col_dict.update({'% Increase':col})
        col += 1
        worksheet.write(row, col, 'SAR Value', header)
        all_col_dict.update({'SAR Value':col})
        col += 1
        for fyear in fy:
            worksheet.write(row, col, 'Bonus \n FY ' + fyear, header)
            all_col_dict.update({'Bonus FY %s' % fyear: col})
            col += 1
        worksheet.write(row, col, '% of Annual Salary', header)
        all_col_dict.update({'% of Annual Salary':col})
        col += 1
        worksheet.write(row, col, 'No. of \n months', header)
        all_col_dict.update({'No of months':col})
        col += 1
        for fyear in fy:
            worksheet.write(row, col, 'TCC \n FY ' + fyear, header)
            all_col_dict.update({'TCC FY %s' % fyear: col})
            col += 1
        worksheet.write(row, col, 'TCC \n FY' + str((int(current_year) + 1)), header)
        all_col_dict.update({'TCC FY %s' % str((int(current_year) + 1)): col})
        col += 1
        for fyear in fy:
            worksheet.write(row, col, 'Dialogue \n FY' + fyear, header)
            all_col_dict.update({'Dialogue FY %s' % fyear:col})
            col += 1
        for fyear in fy:
            worksheet.write(row, col, 'MY PD \n FY' + fyear, header)
            all_col_dict.update({'MY PD FY %s' % fyear:col})
            col += 1
        if bonus_ids:
            for bonus in bonus_ids:
                bonus_dict.update({bonus.id: bonus_dict.get(bonus.id, {})})
                line_dict = {
                     'Employee Name': ' '.join([bonus.employee_id.name or '', bonus.employee_id.middle_name or '', bonus.employee_id.last_name or '']),
                     'Nationality': bonus.country_id.name or '',
                     'Gender': self.get_gender(bonus.gender),
                     'DOJ': bonus.date_of_join or '',
                     'Designation': bonus.job_id.name or '',
                     'Function': bonus.department_id.parent_id.name or '',
                     'Sub Function': bonus.department_id.name or '',
                     'Location': bonus.branch_id.name or '',
                     'Grade': bonus.grade_id.name or ''
                }
                bonus_dict.update({bonus.id: line_dict})
                for bonus_line in bonus.employee_bonus_ids:
                    if bonus_line.fiscalyear_id:
                        fiscal = str(datetime.strptime(bonus_line.fiscalyear_id.date_start, '%Y-%m-%d').year)
                        if fiscal in fy:
                            line_dict.update({'Bonus FY %s' % (str(datetime.strptime(bonus_line.fiscalyear_id.date_start, '%Y-%m-%d').year)): bonus_line.bonus,
                                              'TCC FY %s' % (str(datetime.strptime(bonus_line.fiscalyear_id.date_start, '%Y-%m-%d').year)): bonus_line.tcc,
                                              'Salary FY %s' % (str(datetime.strptime(bonus_line.fiscalyear_id.date_start, '%Y-%m-%d').year)): bonus_line.wage,
                                              'Dialogue FY %s' % (str(datetime.strptime(bonus_line.fiscalyear_id.date_start, '%Y-%m-%d').year)): bonus_line.dialogue or '',
                                              'MY PD FY %s' % (str(datetime.strptime(bonus_line.fiscalyear_id.date_start, '%Y-%m-%d').year)): bonus_line.my_pd or '', })
                            if fiscal == str(current_year):
                                line_dict.update({'% Increase': bonus_line.proposed_hike,
                                                  'Promotion to?': bonus_line.new_job_id and bonus_line.new_job_id.name or ''})
                            bonus_dict.update({bonus.id: line_dict})
        row = actual_data_row = 1
        for plan_dict in bonus_dict.itervalues():
            actual_data_row += 1
            for plan_key in plan_dict.keys():
                if plan_key == 'Promotion to?' or plan_key == '% Increase' or plan_key == 'Bonus FY %s' % current_year or plan_key == 'MY PD FY %s' % current_year:
                    worksheet.write(actual_data_row, all_col_dict.get(plan_key), plan_dict[plan_key], unlocked_details_format)
                else:
                    worksheet.write(actual_data_row, all_col_dict.get(plan_key), plan_dict[plan_key], details_format)
            sar_first = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('Salary FY %s' % str(current_year)))
            sar_last = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('% Increase'))
            worksheet.write_formula(actual_data_row, all_col_dict.get('SAR Value'), '{=SUM(%s*(1+%s))}' % (sar_first, sar_last), details_format)
            bonus_inc_last = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('Salary FY %s' % str(current_year)))
            bonus_inc_first = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('Bonus FY %s' % str(current_year)))
            worksheet.write_formula(actual_data_row, all_col_dict.get('% of Annual Salary'), '{=SUM(%s/(%s*12)}' % (bonus_inc_first, bonus_inc_last), details_format)
            worksheet.write_formula(actual_data_row, all_col_dict.get('No of months'), '{=SUM(%s/%s)}' % (bonus_inc_first, bonus_inc_last), details_format)
            tcc_first = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('SAR Value'))
            tcc_last = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('Bonus FY %s' % str(current_year)))
            worksheet.write_formula(actual_data_row, all_col_dict.get('TCC FY %s' % str((int(current_year) + 1))), '{=SUM(%s*12+%s)}' % (tcc_first, tcc_last), details_format)

        actual_data_row += 2
        worksheet.write(actual_data_row, all_col_dict.get('Salary FY %s' % str(current_year)) - 1, 'Total', totals)
        salary_first = xl_rowcol_to_cell(row + 1, all_col_dict.get('Salary FY %s' % str(current_year)))
        salary_last = xl_rowcol_to_cell(actual_data_row - 2, all_col_dict.get('Salary FY %s' % str(current_year)))
        worksheet.write_formula(actual_data_row, all_col_dict.get('Salary FY %s' % str(current_year)), '{=SUM(%s:%s)}' % (salary_first, salary_last), totals)
        inc_first = xl_rowcol_to_cell(row + 1, all_col_dict.get('% Increase'))
        inc_last = xl_rowcol_to_cell(actual_data_row - 2, all_col_dict.get('% Increase'))
        worksheet.write_formula(actual_data_row, all_col_dict.get('% Increase'), '{=SUM(%s:%s)}' % (inc_first, inc_last), totals)
        sar_value_first = xl_rowcol_to_cell(row + 1, all_col_dict.get('SAR Value'))
        sar_value_last = xl_rowcol_to_cell(actual_data_row - 2, all_col_dict.get('SAR Value'))
        worksheet.write_formula(actual_data_row, all_col_dict.get('SAR Value'), '{=SUM(%s:%s)}' % (sar_value_first, sar_value_last), totals)

        actual_data_row += 2
        worksheet.merge_range(actual_data_row, all_col_dict.get('Salary FY %s' % str(current_year)) - 1, actual_data_row + 1, all_col_dict.get('Salary FY %s' % str(current_year)), 'Budgeted Salary Increases\n - Including Promotions', totals)
        worksheet.merge_range(actual_data_row, all_col_dict.get('% Increase'), actual_data_row + 1, all_col_dict.get('% Increase'), '8%', totals)
        workbook.close()
#         for future use=================
#         export_id = self.pool.get('bonus.report').create(cr, uid, {'type': record.type, 'department_id': record.department_id and record.department_id.id or False,
#              'branch_id': record.branch_id and record.branch_id.id or False, 'excel_file': base64.encodestring(fp.getvalue()), 'filename': filename}, context=context)
        export_id = self.env['bonus.report'].create({'excel_file': base64.encodestring(fp.getvalue()), 'filename': filename})
        fp.close()

        return {
            'name': 'Bonus Report',
            'view_mode': 'form',
            'res_id': export_id,
            'res_model': 'bonus.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
