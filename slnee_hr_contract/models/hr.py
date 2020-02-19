# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def get_active_contracts(self, date=fields.Date.today()):
        """
            get active contracts of employee
        """
        active_contract_ids = self.env['hr.contract'].search([
            '&',
            ('employee_id', '=', self.id),
            '|',
            '&',
            ('date_start', '<=', date),
            '|',
            ('date_end', '>=', date),
            ('date_end', '=', False),
            '|',
            ('trial_date_end', '=', False),
            ('trial_date_end', '>=', date),
            ])
        if active_contract_ids and len(active_contract_ids) > 1:
            raise UserError(_('Too many active contracts for employee %s') % self.name)
        return active_contract_ids
