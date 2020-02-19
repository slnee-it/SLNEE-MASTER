# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models, api, _
import time


class AdminReports(models.TransientModel):
    _name = "admin.reports"

    report = fields.Selection([], string='Report', required=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', domain="[('supplier', '=', True)]",
                                  context="{'default_customer': 0, 'search_default_supplier': 1, 'default_supplier': 1}")
    date_from = fields.Date(string='Date From', default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', dafault=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    filename = fields.Char(string='File Name', size=64)
    excel_file = fields.Binary(string='Excel File')

    @api.multi
    def print_reports(self):
        for report in self:
            if report.report == 'travel':
                return self.print_travel_report()
            elif report.report == 'hotel':
                return self.print_hotel_report()
            elif report.report == 'copy_center':
                return self.print_copy_center_report()
        return True

    def return_wiz_action(self, res_id, context=None):
        return {
            'name': 'Admin Reports',
            'view_mode': 'form',
            'res_id': res_id,
            'res_model': 'admin.reports',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }
