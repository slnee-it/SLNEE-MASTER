
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BudgetAdjust(models.Model):
    _name = 'budget.adjust'
    _description ='Budget Adjustment'
    _inherit = ['mail.thread', 'mail.activity.mixin']



    date = fields.Date(string='Date', default=fields.Date.today())
    name = fields.Char(string='Name', default='/',copy=False)
    type = fields.Selection([('in',_('IN')),('out',_('OUT'))],required=True, string='Type')
    section_id = fields.Many2one('crossovered.budget.lines.sections', string='Section Name', required=True)
    budget_id = fields.Many2one('crossovered.budget', string='Budget', required=True)

    budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Line')
    amount = fields.Float(string='Amount')
    state = fields.Selection([('draft',_('Draft')),
                              ('confirm',_('Confirmed')),
                              ('approve',_('Approved')),
                              ('reverse',_('Reversed')),
                              ('refuse',_('Refused')),
                              ('cancel',_('Cancelled')),
                              ], string='State', default='draft')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    reason = fields.Text(string='Transfer Reasons')

    @api.multi
    def reverse_adjust(self):
        if self.type == 'in' and self.budget_line_id.funds_check(self.amount) :
            self.budget_line_id.sudo().write(
                {'adjust_in_amount': self.budget_line_id.adjust_in_amount - self.amount})
        else:
            self.budget_line_id.sudo().write(
                {'adjust_out_amount': self.budget_line_id.adjust_out_amount - self.amount})

    @api.multi
    def update_budget_line(self):
        if self.type == 'out' and self.budget_line_id.funds_check(self.amount) :
            self.budget_line_id.sudo().write(
                {'adjust_out_amount': self.budget_line_id.adjust_out_amount + self.amount})
        else:
            self.budget_line_id.sudo().write(
                {'adjust_in_amount': self.budget_line_id.adjust_in_amount + self.amount})

    @api.multi
    def action_confirm(self):
        for rec in self:
            if rec.budget_line_id.funds_check(self.amount):
                name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.date).next_by_code('budget.adjust') or '/'
                rec.write({'name':name,'state': 'confirm'})

    @api.multi
    def action_approve(self):
        self.update_budget_line()
        for rec in self:
            rec.write({'state': 'approve'})

    @api.multi
    def action_refuse(self):
        for rec in self:
            rec.write({'state': 'refuse'})

    @api.multi
    def action_reverse(self):
        self.reverse_adjust()
        for rec in self:
            rec.write({'state': 'reverse'})

    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    @api.multi
    def action_redraft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can not delete record"))
        return super(BudgetAdjust, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        name = _('Budget Adjustment')
        for rec in self:
            if rec.name:
                name = rec.name + '-' + name
            result.append((rec.id, name))
        return result


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    adjust_in_amount = fields.Float(string='Adjustment IN', readonly=True, copy=False)
    adjust_out_amount = fields.Float(string='Adjustment OUT', readonly=True, copy=False)
    adjust_in_ids = fields.One2many('budget.adjust', 'budget_line_id',domain=[('type','=','in')] ,string='Adjustment IN operations')
    adjust_out_ids = fields.One2many('budget.adjust', 'budget_line_id',domain=[('type','=','out')],string='Adjustment OUT operations')


