
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    prevent_supplier_outstanding_payment = fields.Boolean(string='Prevent outstanding payment for supplier')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            prevent_supplier_outstanding_payment =self.env['ir.config_parameter'].sudo().get_param('payment_control.prevent_supplier_outstanding_payment')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('payment_control.prevent_supplier_outstanding_payment', self.prevent_supplier_outstanding_payment)
