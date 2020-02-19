from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _

from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    encumb_id = fields.Many2one('encumb.order', string='Encumberance Order', copy=False,domain=[('state','=','approve')])

    @api.multi
    @api.constrains('encumb_id', 'order_line','order_line.account_analytic_id', 'order_line.price_subtotal_signed')
    def _check_encumb_id(self):
        """
        This constrain to ensure the encumberance is sufficient for all the purchase lines amount

        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('budget_management.allow_encumber_and_funds_check'):
            for rec in self:
                if rec.encumb_id:
                    diff_currency = False
                    if rec.currency_id.id != self.env.user.company_id.currency_id.id:
                        diff_currency = True
                    for line in rec.order_line:
                        encumb_line_ids = self.env['encumb.order.line'].search([('order_id','=',rec.encumb_id.id),('analytic_account_id','=',line.account_analytic_id.id)])

                        result = 0
                        for enc_line in encumb_line_ids:
                            result += enc_line.remaining_amount
                        amount = line.price_total
                        if diff_currency:
                            amount = rec.currency_id.with_context(date=rec.date_approve).compute(line.price_total,self.env.user.company_id.currency_id)
                        if result < amount:
                            raise ValidationError(
                                _('There is no enough encumbered amount for the line with analytic account %s') % (
                                    line.account_analytic_id.name))

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            if not rec.encumb_id and not self.env['ir.config_parameter'].sudo().get_param('budget_management.module_bills_encumberance'):
                raise ValidationError(_('Please add Encumberance Order before confirming this purchase order'))
            if not rec.encumb_id and self.env['ir.config_parameter'].sudo().get_param('budget_management.module_bills_encumberance'):
                rec.encumb_id = self.env['encumb.order'].create_po_encumb(rec)
        return res

    @api.multi
    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        res['context']['default_encumb_id'] = self.encumb_id.id
        return res

    @api.multi
    def po_fund_check(self):
        for rec in self:
            date_order = rec.date_order or fields.Date.today()
            self.env.cr.execute("""
                SELECT SUM(price_total) , account_analytic_id
                FROM purchase_order_line WHERE order_id = %s GROUP BY account_analytic_id  """, (rec.id,))
            result = self.env.cr.fetchall() or False
            for (amount, analytic_account_id) in result:
                self.env.cr.execute("""
                                SELECT SUM(remain_amount)
                                FROM crossovered_budget_lines WHERE date_from < %s and date_to > %s and analytic_account_id = %s GROUP BY analytic_account_id  """,
                                    (date_order, date_order, analytic_account_id))
                result = self.env.cr.fetchone()[0] or False
                if result < amount:
                    analytic_account = self.env['account.analytic.account'].browse(analytic_account_id)
                    raise ValidationError(
                        _('No enough fund for lines with analytic account %s ') % (analytic_account.name))
        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True)
