

from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError

class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"


    @api.constrains('account_ids')
    def check_account_unique(self):
        """
        constrain to prevent general ledger account from being repeated in different budget position

        """
        for rec in self:
            result = False
            for account in rec.account_ids:
                self.env.cr.execute("""
                                    SELECT COUNT(account_id)
                                    FROM account_budget_rel
                                    WHERE account_id=%s
                                        """,
                                    (account.id,))
                result = self.env.cr.fetchone()[0] or False
                if result > 1:
                    raise ValidationError(_('You can not choose the account "%s" because it exists in another budget position .')%(account.name))