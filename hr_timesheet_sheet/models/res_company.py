# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from dateutil.rrule import (MONTHLY, WEEKLY, DAILY)


class ResCompany(models.Model):
    _inherit = 'res.company'

    sheet_range = fields.Selection([
        (MONTHLY, 'Month'),
        (WEEKLY, 'Week'),
        (DAILY, 'Day')],
        string='Timesheet Sheet Range',
        default=WEEKLY,
        help="The range of your Timesheet Sheet.")
