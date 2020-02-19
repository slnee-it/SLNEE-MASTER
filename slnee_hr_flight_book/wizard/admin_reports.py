# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from io import BytesIO
from datetime import datetime
import base64
from odoo import fields, models, api ,_
import xlsxwriter

class AdminReports(models.TransientModel):
    _inherit = "admin.reports"

    report = fields.Selection(selection_add=[('travel', 'Travel')])
    supplier_id = fields.Many2one('res.partner', string='Supplier', domain="[('supplier', '=', True)]",
                                  context="{'default_customer': 0, 'search_default_supplier': 1, 'default_supplier': 1}")

    @api.multi
    def print_travel_report(self):
        flight_line_obj = self.env['flight.booking.line']
        self.ensure_one()
        report = self
        filename = 'Travel Report.xlsx'
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Travel')
        detail_head = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 12,
                    'num_format': '#,##0.00',
                    'font_name': 'Times New Roman'})
        details_format = workbook.add_format({
                                            'font_size': 12,
                                            'valign': 'vcenter',
                                            'num_format': '#,##0.00',
                                            'font_name': 'Times New Roman'})

        # # Preparing Dictionary for report
        travel_dict = {}
        domain = []
        if report.date_from:
            domain.append(('travel_date', '>=', report.date_from))
        if report.date_to:
            domain.append(('travel_date', '<=', report.date_to))
        if report.supplier_id:
            domain.append(('booking_id.supplier_id', '=', report.supplier_id.id))
        flight_line_ids = flight_line_obj.search(domain)
        for flight_line in flight_line_ids:
            travel_dict.update({flight_line.id: travel_dict.get(flight_line.id, {})})
            line_dict = {'po_number': flight_line.booking_id.po_number or '',
                         'destination': (flight_line.source + '/' + flight_line.destination) or '',
                         'ticket_no': flight_line.ticket_no or '',
                         'employee': flight_line.booking_id.employee_id.name or '',
                         'travel_date': flight_line.travel_date or '',
                         'class': flight_line.flight_class or '',
                         'airline': flight_line.airline.name or '',
                         'invoice_amount': flight_line.invoice_amount,
                         'remarks': flight_line.remarks or ''}
            travel_dict.update({flight_line.id: line_dict})

        worksheet.write(0, 3, 'Report ', detail_head)
        worksheet.write(0, 4, 'Flight Booking', detail_head)
        worksheet.write(1, 3, 'Prepared on', detail_head)
        worksheet.write(2, 3, 'Prepared by', detail_head)
        worksheet.write(1, 4, datetime.strftime(datetime.now(), '%Y-%m-%d'), details_format)
        worksheet.write(2, 4, self.env['res.users'].browse(self.env.uid).name, details_format)

        worksheet.write(3, 0, 'PO Number', detail_head)
        worksheet.write(3, 1, 'ROUTING', detail_head)
        worksheet.write(3, 2, 'TICKET/S NO.', detail_head)
        worksheet.write(3, 3, 'PASSENGER/S', detail_head)
        worksheet.write(3, 4, 'TRAVEL DATE', detail_head)
        worksheet.write(3, 5, 'CLASS', detail_head)
        worksheet.write(3, 6, 'AIRLINE', detail_head)
        worksheet.write(3, 7, 'INVOICE AMOUNT', detail_head),
        worksheet.write(3, 8, 'REMARKS', detail_head),

        all_col_dict = {'po_number': 0, 'destination': 1, 'ticket_no': 2, 'employee': 3, 'travel_date': 4,
                        'class': 5, 'airline': 6, 'invoice_amount': 7, 'remarks': 8}

        worksheet.set_row(3, 45)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 18)
        worksheet.set_column(3, 3, 18)
        worksheet.set_column(4, 4, 20)
        worksheet.set_column(6, 6, 18)
        worksheet.set_column(7, 7, 22)
        worksheet.set_column(8, 8, 20)
        worksheet.freeze_panes(4, 9)
        actual_data_row = 3
        for line_dict in travel_dict.values():
            actual_data_row += 1
            for line_key in line_dict.keys():
                worksheet.write(actual_data_row, all_col_dict.get(line_key), line_dict[line_key], details_format)
        workbook.close()
        report.write({'excel_file': base64.encodestring(fp.getvalue()), 'filename': filename})
        fp.close()

        return self.return_wiz_action(report.id)
