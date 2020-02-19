# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit='res.company'

    payment_order_amount_limit = fields.Float('Amount in Payment order so SG can approve With Service Manager',
                                             default=30000)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_order_amount_limit = fields.Float('Amount in Payment order so SG can approve With Service Manager', readonly=False,
                                              company_dependent=True, related='company_id.payment_order_amount_limit')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            payment_order_amount_limit=float(params.get_param('slnee_payment_correlation.payment_order_amount_limit', default=30000))
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('slnee_payment_correlation.payment_order_amount_limit',
                                                         self.payment_order_amount_limit)

