
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    encumb_id = fields.Many2one('encumb.order',string='Encumberance Order',copy=False,domain=[('state','=','approve')])

    @api.multi
    @api.constrains('encumb_id','invoice_line_ids','invoice_line_ids.price_subtotal_signed')
    def _check_encumb_id(self):
        """
        This constrain to ensure the encumberance is sufficient for all the invoice lines amount

        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('budget_management.allow_encumber_and_funds_check') and not self.env['ir.config_parameter'].sudo().get_param('budget_management.module_bills_encumberance'):
            for rec in self:
                for line in rec.invoice_line_ids:
                    if not rec.encumb_id:
                        raise ValidationError(
                            _('Please set encumberance order for this vendor bill'))
                    date_invoice = rec.date_invoice or fields.Date.today()
                    self.env['encumb.order'].check_combination_budget(line.account_id, line.account_analytic_id,
                                                                      date_invoice)
                    #self.env.cr.execute("""
                    #                    SELECT SUM(remaining_amount)
                    #                    FROM encumb_order_line
                    #                    WHERE order_id=%s
                    #                        and analytic_account_id = %s """,
                    #                    (rec.encumb_id.id,line.account_analytic_id.id,))
                    encumb_line_ids = self.env['encumb.order.line'].search([('order_id', '=', rec.encumb_id.id),('analytic_account_id', '=', line.account_analytic_id.id)])
                    result = 0
                    for enc_line in encumb_line_ids:
                        result += enc_line.remaining_amount
                    #result = self.env.cr.fetchone()[0] or False
                    if result < line.price_subtotal_signed:
                        raise ValidationError(
                            _('There is no enough encumbered amount for the line with analytic account %s')%(line.account_analytic_id.name))

    @api.multi
    def action_invoice_open(self):
        for rec in self:
            self.env['encumb.order'].release_inv_encumb(rec)
            res = super(AccountInvoice, self).action_invoice_open()
            if not rec.encumb_id.origin:
                rec.encumb_id.origin = rec.number
            else:
                source = rec.encumb_id.origin
                rec.encumb_id.origin = source +' , '+rec.number
        return res

    @api.multi
    def inv_fund_check(self):
        for rec in self:
            self.env.cr.execute("""
            SELECT SUM(price_subtotal_signed) , account_analytic_id
            FROM account_invoice_line WHERE invoice_id = %s GROUP BY account_analytic_id  """,(rec.id, ))
            result = self.env.cr.fetchall() or False
            for (amount,analytic_account_id) in result:
                date_invoice = rec.date_invoice or fields.Date.today()
                self.env.cr.execute("""
                            SELECT SUM(remain_amount)
                            FROM crossovered_budget_lines WHERE date_from < %s and date_to > %s and analytic_account_id = %s GROUP BY analytic_account_id  """,
                                    (date_invoice,date_invoice,analytic_account_id))
                result = self.env.cr.fetchone()[0] or False
                if result < amount:
                    analytic_account = self.env['account.analytic.account'].browse(analytic_account_id)
                    raise ValidationError(_('No enough fund for lines with analytic account %s ')%(analytic_account.name))
        return True

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    account_analytic_id = fields.Many2one('account.analytic.account',string='Analytic Account',required=True)