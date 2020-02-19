

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import operator as py_operator


class EncumbOrder(models.Model):
    _inherit = 'encumb.order'

    po_ids = fields.One2many('purchase.order', 'encumb_id', string='Purchase Order')

    @api.model
    def create_po_encumb(self, po):
        encumb_lines = []
        # raise ValidationError(_(str( invoice['partner_id'])))
        for line in po['order_line']:
            values = {
                'name': line.name,
                'date': po['date_order'] or fields.Date.today(),
                'account_id': self.get_account(line.product_id).id,
                'analytic_account_id': line.account_analytic_id.id,
                'encumbered_amount': line.price_total,
                'reserved_amount': line.price_total,
            }
            encumb_lines.append((0, 0, values))
        values = {
            'name': 'Auto Encumberance for Purchase Order',
            'type': 'po',
            'date': po['date_order'] or fields.Date.today(),
            'partner_id': po['partner_id'].id,
            'encumbered_amount': po['amount_total'],
            'consumed_amount': 0,
            'encumb_line_ids': encumb_lines,
            'origin': po['name'],
        }

        encumb_id = self.create(values)
        encumb_id.button_confirm()
        encumb_id.button_approve()
        return encumb_id



class EncumberanceOrderLine(models.Model):
    _inherit = 'encumb.order.line'

    @api.multi
    @api.depends('order_id.invoice_ids','order_id.invoice_ids.state','order_id.invoice_ids.invoice_line_ids','order_id.invoice_ids.invoice_line_ids.account_analytic_id','order_id.invoice_ids.invoice_line_ids.price_subtotal_signed','order_id.po_ids','order_id.po_ids.state','order_id.po_ids.order_line','order_id.po_ids.order_line.account_analytic_id','order_id.po_ids.order_line.price_total')
    def _compute_reserved_amount(self):
        total = 0
        for rec in self:
            for invoice in rec.order_id.invoice_ids:
                if invoice.state != 'draft':
                    continue
                else:
                    for line in invoice.invoice_line_ids:
                        if line.account_analytic_id.id == rec.analytic_account_id.id:
                            total += line.price_subtotal_signed
            for po in rec.order_id.po_ids:
                if po.state == 'draft' :
                    continue
                else:
                    for line in po.order_line:
                        if line.account_analytic_id.id == rec.analytic_account_id.id:
                            total += line.price_total - (line.qty_invoiced * line.price_unit)
            rec.reserved_amount = total
            rec.remaining_amount = rec.encumbered_amount - rec.reserved_amount - rec.released_amount
            #if not rec.is_released:
                #rec.remaining_amount = rec.encumbered_amount - rec.reserved_amount - rec.released_amount
                #if rec.remaining_amount == 0 and rec.released_amount == rec.encumbered_amount:
                    #rec.is_released = True
