# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_group_company_branch = fields.Boolean(string="Multi Branch", implied_group='slnee_hr_branch.group_company_branch')
