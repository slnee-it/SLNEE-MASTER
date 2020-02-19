from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    encumb_id = fields.Many2one('encumb.order',string='Encumber',copy=False)

    @api.multi
    def move_fund_check(self):
        for rec in self:
            date = rec.date or fields.Date.today()

            self.env.cr.execute("""
                    SELECT SUM(debit) , analytic_account_id
                    FROM account_move_line WHERE move_id = %s GROUP BY analytic_account_id  """, (rec.id,))
            result = self.env.cr.fetchall() or False
            for (amount, analytic_account_id) in result:
                self.env.cr.execute("""
                                    SELECT SUM(remain_amount)
                                    FROM crossovered_budget_lines WHERE date_from < %s and date_to > %s and analytic_account_id = %s GROUP BY analytic_account_id  """,
                                    (date, date, analytic_account_id))
                result = self.env.cr.fetchone() or False
                if result and result[0] < amount:
                    analytic_account = self.env['account.analytic.account'].browse(analytic_account_id)
                    raise ValidationError(
                        _('No enough fund for lines with analytic account %s ') % (analytic_account.name))
        return True

    @api.multi
    def post(self):
        for rec in self:
            if rec.move_fund_check():
                return super(AccountMove, self).post()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',required=True)

    @api.multi
    @api.constrains('account_id','analytic_account_id')
    def _check_analytic_account(self):
        """
        This constrain to ensure the analytic account is set if the fund check is activated

        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('budget_management.allow_encumber_and_funds_check'):

            for rec in self:
                date = rec.date or fields.Date.today()
                self.env['encumb.order'].check_combination_budget(rec.account_id, rec.analytic_account_id, date)
                if rec.account_id.user_type_id.name == 'Expenses' and not rec.analytic_account_id:
                    raise ValidationError(_('Please set analytic account for the lines with account %s')%(rec.account_id.name))
                elif rec.account_id.user_type_id.name == 'Expenses':
                    self.env.cr.execute("""
                                                        SELECT budget_id
                                                        FROM account_budget_rel
                                                        WHERE account_id=%s
                                                            """,
                                        (rec.account_id.id,))
                    result = self.env.cr.fetchone() or False
                    if not result:
                        raise ValidationError(
                            _('The account "%s" is not linked to any budget position')%(rec.account_id.name))
