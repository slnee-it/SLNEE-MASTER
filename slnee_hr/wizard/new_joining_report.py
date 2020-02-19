# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta


class NewJoiningEmployeeReports(models.TransientModel):
    _name = "joining.employee.reports"

    @api.model
    def default_get(self, fields_list):
        """
            Override method for get default values
        """
        res = super(NewJoiningEmployeeReports, self).default_get(fields_list)
        current_date = datetime.strptime(str(fields.Date.today()), DEFAULT_SERVER_DATE_FORMAT).date()
        res.update({
                'start_date': current_date + relativedelta(day=1),
                'end_date': current_date + relativedelta(day=1, months=+1, days=-1),
            })
        return res

    start_date = fields.Date(string='Start Date', default=datetime.now(), required=True)
    end_date = fields.Date(string='End Date', default=datetime.now(), required=True)

    _sql_constraints = [
        ('date_check', "CHECK((start_date <= end_date))", "Please enter valid date")
    ]

    @api.multi
    def print_reports(self):
        data = self.read()[0]
        return self.env.ref('slnee_hr.action_report_joining_employee').report_action(self, data=data)
