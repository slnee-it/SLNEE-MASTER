# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    survey_id = fields.Many2one('survey.survey', related='company_id.survey_id', string="Survey")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        survey_id = params.get_param('base_setup.survey_id', default=False)
        if survey_id:
            res.update({'survey_id': survey_id.id})
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.survey_id:
            self.env['ir.config_parameter'].sudo().set_param("base_setup.survey_id", self.survey_id.id)
