
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrossoveredBudgetLinesSections(models.Model):
    _name = "crossovered.budget.lines.sections"
    _description = "Budget Line Sections"

    name = fields.Char(string="Description")
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self:self.env.user.company_id.id)

class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    @api.model
    def funds_check(self, amount):
        if not self.env['ir.config_parameter'].sudo().get_param('budget_management.allow_encumber_and_funds_check'):
            return True
        for rec in self:
            if rec.remain_amount < amount:
                raise ValidationError(_("There is no enough budget for this operation !"))
            else:
                return True


    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.general_budget_id.name
            result.append((record.id, name))
        return result

    section_id = fields.Many2one('crossovered.budget.lines.sections', string='Section Name')
    remain_amount = fields.Float(string='Remaining Amount',readonly=True, compute='_compute_remain_amount')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], 'Status', default='draft', related='crossovered_budget_id.state')

    @api.depends('planned_amount','amount_transfer_out', 'amount_transfer_in', 'adjust_in_amount', 'adjust_out_amount','encumbered_amount','practical_amount')
    def _compute_remain_amount(self):
        """
        compute the remaining amount in budget line from adjustment , transfer , encumberance and Actual consuming
        :return:
        """
        for rec in self:
            planned_amount = rec.planned_amount or 0
            amount_transfer_in = rec.amount_transfer_in or 0
            amount_transfer_out = rec.amount_transfer_out or 0
            adjust_in_amount = rec.adjust_in_amount or 0
            adjust_out_amount = rec.adjust_out_amount or 0
            encumbered_amount = rec.encumbered_amount
            practical_amount = rec.practical_amount

            rec.remain_amount = planned_amount + practical_amount + amount_transfer_in - amount_transfer_out + adjust_in_amount - adjust_out_amount - encumbered_amount
