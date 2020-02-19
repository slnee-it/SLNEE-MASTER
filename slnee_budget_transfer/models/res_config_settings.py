# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_percentage_while_transfer = fields.Boolean(string='Apply Conditions  While Budget Transfer')
    percentage_to_approve_source_avil_amount = fields.Float(related='company_id.percentage_to_approve_source_avil_amount', readonly=False)
    percentage_to_check_trans_amount_to_planned = fields.Float(related='company_id.percentage_to_check_trans_amount_to_planned', readonly=False)



