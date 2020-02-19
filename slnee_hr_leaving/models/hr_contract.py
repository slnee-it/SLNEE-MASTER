# Part of odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _

class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    notice_start_date = fields.Date('Notice Start Date',readonly=True)
    notice_end_date = fields.Date('Notice End Date',readonly=True)
    is_leaving = fields.Boolean('Leaving Notice')
