# -*- coding: utf-8 -*-


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

    cap = fields.Float(related="analytic_account_id.cap",string="Cap")
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount')
    correlated_amount = fields.Float(string="Encumbrance Amount", copy=False)
    correlation_percentage = fields.Float(string='Encumbrance Percentage(%)', compute='_compute_correlation_percentage')
    consumed_amount = fields.Float(string='Consumed Amount')
    remaining_amount = fields.Float(string='Remaining amount', compute='_compute_remaining_amount')
    remaining_without_correlation = fields.Float(string='Available For Encumbrance', compute='_compute_available_for_correlation')
    remaining_without_correlation_perc = fields.Float(string='Available (%)', compute='_compute_available_for_correlation')
    section_id = fields.Many2one('crossovered.budget.lines.sections', string='Section Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], 'Status', default='draft', related='crossovered_budget_id.state')

    

    @api.depends('planned_amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.planned_amount

    @api.depends('total_amount', 'correlated_amount')
    def _compute_correlation_percentage(self):
        for rec in self:
            rec.correlation_percentage = rec.correlated_amount and rec.total_amount and (rec.correlated_amount/rec.total_amount)*100.0

    @api.depends('consumed_amount', 'correlated_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.correlated_amount - rec.consumed_amount

    @api.depends('total_amount', 'correlated_amount')
    def _compute_available_for_correlation(self):
        for rec in self:
            rec.remaining_without_correlation = rec.total_amount - rec.correlated_amount
            rec.remaining_without_correlation_perc = rec.total_amount and ((rec.total_amount - rec.correlated_amount) / rec.total_amount) *100

    def check_cap(self):
        total_allocated_amount = 0.00
        for line_rec in self.search([('analytic_account_id', '=', self.analytic_account_id.id)]):
            total_allocated_amount += line_rec.total_amount
        if total_allocated_amount > self.cap:
            raise ValidationError(_("You have exceed cap amount for %s project." % self.analytic_account_id.name))
        return True

    @api.model
    def create(self, vals):
        rec = super(CrossoveredBudgetLines, self).create(vals)
        rec.check_cap()
        return rec
    
    @api.model
    def write(self, vals):
        rec = super(CrossoveredBudgetLines, self).write(vals)
        for rec in self:
            rec.check_cap()
        return rec 

class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    cap = fields.Float("Cap")

class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"


    @api.one
    @api.constrains('crossovered_budget_line','crossovered_budget_line.analytic_account_id','crossovered_budget_line.section_id','crossovered_budget_line.general_budget_id','crossovered_budget_line.date_from','crossovered_budget_line.date_to')
    def check_time_elapse(self):
        count = 0
        for line in self.crossovered_budget_line:
            count += 1
            analytic_account = line.analytic_account_id
            section = line.section_id
            budget_position = line.general_budget_id
            date_from = line.date_from
            date_to = line.date_to
            for rest in self.crossovered_budget_line[count:]:
                if analytic_account.id == rest.analytic_account_id.id and section.id == rest.section_id.id and budget_position.id == rest.general_budget_id.id and ((date_from >= rest.date_from and date_from <= rest.date_to) or (date_to >= rest.date_from and date_to <= rest.date_to)):            
                    raise ValidationError(_("There is time elapse !!"))
