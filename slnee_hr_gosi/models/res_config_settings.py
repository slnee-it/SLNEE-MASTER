# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    calculate_hadaf = fields.Boolean("Hide Password")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        calculate_hadaf = params.get_param('base_setup.calculate_hadaf', default=False)
        res.update({'calculate_hadaf': calculate_hadaf,})
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("base_setup.calculate_hadaf", self.calculate_hadaf)
