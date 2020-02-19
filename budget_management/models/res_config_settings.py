
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_encumber_and_funds_check = fields.Boolean(string='Activate Encumberance and funds check')
    module_bills_encumberance = fields.Boolean(string='Activate Auto Encumberance')
    module_purchase_encumberance = fields.Boolean(string='Activate Encumberance for Purchase Orders')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            allow_encumber_and_funds_check =self.env['ir.config_parameter'].sudo().get_param('budget_management.allow_encumber_and_funds_check'),
            module_bills_encumberance=self.env['ir.config_parameter'].sudo().get_param(
                'budget_management.module_bills_encumberance'),
        module_purchase_encumberance = self.env['ir.config_parameter'].sudo().get_param(
            'budget_management.module_purchase_encumberance'),

        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('budget_management.allow_encumber_and_funds_check', self.allow_encumber_and_funds_check)
        self.env['ir.config_parameter'].sudo().set_param('budget_management.module_bills_encumberance', self.module_bills_encumberance)
        self.env['ir.config_parameter'].sudo().set_param('budget_management.module_purchase_encumberance',
                                                         self.module_purchase_encumberance)

    @api.onchange('module_purchase_encumberance')
    def onchange_module_purchase_encumberance(self):
        if self.module_purchase_encumberance:
            self.group_analytic_account_for_purchases = True

    @api.onchange('allow_encumber_and_funds_check')
    def onchange_allow_encumber_and_funds_check(self):
        if self.allow_encumber_and_funds_check:
            self.module_purchase_encumberance = True
