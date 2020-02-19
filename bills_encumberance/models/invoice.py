
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"



    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if not res['encumb_id']:
            encumb_id = self.env['encumb.order'].create_inv_encumb(res)
            res.update({'encumb_id':encumb_id})
        return res