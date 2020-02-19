

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        """
        Editing the post function of payment to prevent outstanding payment

        :return:
        """
        for rec in self:
            partner_balance = rec.partner_id.debit - rec.partner_id.credit
            prevent_out_payment = self.env['ir.config_parameter'].sudo().get_param('payment_control.prevent_supplier_outstanding_payment')
            if prevent_out_payment and self.payment_type == 'outbound' and rec.amount and partner_balance < rec.amount :
                raise ValidationError(_("The payment amount is greater than the partner balance "))
        return super(account_payment, self).post()