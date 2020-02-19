# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    use_percentage_while_transfer = fields.Boolean(string='Apply Conditions  While Budget Transfer')
    percentage_to_approve_source_avil_amount = fields.Float(readonly=False)
    percentage_to_check_trans_amount_to_planned = fields.Float(readonly=False)
