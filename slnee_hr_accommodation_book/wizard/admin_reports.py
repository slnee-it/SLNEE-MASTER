# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from io import BytesIO
from datetime import datetime
import base64
from odoo import fields, models, api
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


class AdminReports(models.TransientModel):
    _inherit = "admin.reports"

    report = fields.Selection(selection_add=[('hotel', 'Hotel')])
    type = fields.Selection([('villa', 'Villa'), ('hotel', 'Hotel')], 'Stay In',)

    def print_hotel_report(self):
        accommodation_line_obj = self.env['accommodation.line']
        report = self
        filename = 'Hotel Report.xlsx'
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Hotel')
        detail_head = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})
        details_format = workbook.add_format({
                    'valign': 'vcenter',
                    'font_size': 12,
                    'valign': 'vcenter',
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})

        # # Preparing Dictionary for report
        hotel_dict = {}
        domain = []
        if report.date_from:
            domain.append(('check_out_time', '>=', report.date_from))
        if report.date_to:
            domain.append(('check_out_time', '<=', report.date_to))
        if report.type:
            domain.append(('stay_type', '=', report.type))
        accommodation_lines = accommodation_line_obj.search(domain)
        for accommodation_line in accommodation_lines:
            hotel_dict.update({accommodation_line.id: hotel_dict.get(accommodation_line.id, {})})
            line_dict = {'employee': accommodation_line.accommodation_id.employee_id.name or '', 'type': accommodation_line.stay_type,
                         'villa': accommodation_line.villa_id.name or '-', 'hotel': accommodation_line.hotel_id.name or '-',
                         'city': accommodation_line.accommodation_id.city or '', 'check-in': accommodation_line.check_in_time,
                         'check-out': accommodation_line.check_out_time, 'days': accommodation_line.days,
                         'amount': accommodation_line.amount, 'reason': accommodation_line.accommodation_id.reason_id and accommodation_line.accommodation_id.reason_id.name or '',
                         }
            hotel_dict.update({accommodation_line.id: line_dict})

        worksheet.write(0, 3, 'Report ', detail_head)
        worksheet.write(0, 4, 'Accommodation', detail_head)
        worksheet.write(1, 3, 'Prepared on', detail_head)
        worksheet.write(2, 3, 'Prepared by', detail_head)
        worksheet.write(1, 4, datetime.strftime(datetime.now(), '%Y-%m-%d'), details_format)
        worksheet.write(2, 4, self.env['res.users'].browse(self.env.uid).name, details_format)

        worksheet.write(3, 0, 'Employee', detail_head)
        worksheet.write(3, 1, 'Type', detail_head)
        worksheet.write(3, 2, 'Villa', detail_head)
        worksheet.write(3, 3, 'Hotel', detail_head)
        worksheet.write(3, 4, 'City', detail_head)
        worksheet.write(3, 5, 'Check-In', detail_head)
        worksheet.write(3, 6, 'Check-Out', detail_head),
        worksheet.write(3, 7, 'Number of \n Nights', detail_head),
        worksheet.write(3, 8, 'Invoice \n Amount', detail_head),
        worksheet.write(3, 9, 'Reason', detail_head),
        worksheet.write(3, 10, 'Remarks', detail_head),
        first_row = 3
        all_col_dict = {'employee': 0, 'type': 1, 'villa': 2, 'hotel': 3, 'city': 4, 'check-in': 5,
                        'check-out': 6, 'days': 7, 'amount': 8, 'reason': 9, 'remarks': 11}

        worksheet.set_row(3, 45)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(2, 4, 12)
        worksheet.set_column(5, 6, 15)
        worksheet.set_column(7, 8, 11)
        worksheet.set_column(9, 10, 15)
        worksheet.set_column(11, 11, 25)
        worksheet.freeze_panes(4, 0)
        actual_data_row = 3
        for line_dict in hotel_dict.values():
            actual_data_row += 1
            for line_key in line_dict.keys():
                worksheet.write(actual_data_row, all_col_dict.get(line_key), line_dict[line_key], details_format)
        worksheet.set_row(actual_data_row + 1, 30, detail_head)
        service_first = xl_rowcol_to_cell(first_row + 1, all_col_dict.get('amount'))
        service_last = xl_rowcol_to_cell(actual_data_row, all_col_dict.get('amount'))
        worksheet.write_formula(actual_data_row + 1, all_col_dict.get('amount'), '{=SUM(%s:%s)}' % (service_first, service_last), detail_head)
        workbook.close()
        report.write({'excel_file': base64.encodestring(fp.getvalue()), 'filename': filename})
        fp.close()

        return self.return_wiz_action(report.id)
