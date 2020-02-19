from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EncumbOrder(models.Model):
    _inherit = 'encumb.order'

    @api.model
    def create_inv_encumb(self, invoice):
        if invoice.type != 'in_invoice':
            return False
        encumb_lines = []
        #raise ValidationError(_(str( invoice['partner_id'])))
        for line in invoice['invoice_line_ids']:

            values = {
                'name' : line.name,

                'date': invoice['date_invoice'] or fields.Date.today(),
                'account_id':line.account_id.id,
                'analytic_account_id':line.account_analytic_id.id,
                'encumbered_amount': line.price_subtotal_signed,
                'reserved_amount': line.price_subtotal_signed,
            }
            encumb_lines.append((0,0,values))
        values = {
            'name' : 'Auto Encumberance for draft invoice',
            'type': 'bill',
        'date' : invoice['date_invoice'] or fields.Date.today(),
        'partner_id' : invoice['partner_id'].id,
        'encumbered_amount' : invoice['amount_total'],
        'consumed_amount' : 0,
        'encumb_line_ids' : encumb_lines,
        }

        encumb_id = self.create(values)
        encumb_id.button_confirm()
        encumb_id.button_approve()
        return encumb_id

    @api.multi
    @api.depends('encumb_line_ids.encumbered_amount')
    def _compute_amount(self):
        for rec in self:
            rec.encumbered_amount = sum(col.encumbered_amount for col in rec.encumb_line_ids)
