# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    sheet_range = fields.Selection(
        related='company_id.sheet_range',
        string="Timesheet Sheet Range",
        help="The range of your Timesheet Sheet.")
