# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import operator as py_operator

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}

class CorrelationOrder(models.Model):
    _name = 'correlation.order'
    _description = 'Encumbrance Order'
    _inherit = ['mail.thread']

    code = fields.Char(string='Code', default='/')
    date = fields.Date(string='Date', default=fields.Date.today())
    name = fields.Char(string='Description')
    partner_id = fields.Many2one('res.partner', string='Beneficiary Name')
    required_amount = fields.Float(string='Required Amount', compute='_compute_amount')
    correlated_amount = fields.Float(string='Encumbrance Amount', compute='_compute_amount')
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_amount')
    origion = fields.Char(string='Origin')
    correlation_order_line = fields.One2many('correlation.order.line', 'order_id', string='Encumbrance Order Details')
    state = fields.Selection([('draft', _('Draft')),
                              ('confirm', _('Confirmed')),
                              ('approve', _('Approved')),
                              ('refuse', _('Refused')),
                              ('cancel', _('Cancelled'))], string='State', default='draft')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id)
    is_closed = fields.Boolean(string='Is CLosed', compute='_compute_is_closed', search='_search_is_closed')

    @api.multi
    @api.depends('correlation_order_line.required_amount', 'correlation_order_line.remaining_amount')
    def _compute_amount(self):
        for rec in self:
            rec.required_amount = sum(col.required_amount for col in rec.correlation_order_line)
            rec.correlated_amount = sum(col.correlated_amount for col in rec.correlation_order_line)
            rec.remaining_amount = sum(col.remaining_amount for col in rec.correlation_order_line)

    @api.depends('remaining_amount')
    def _compute_is_closed(self):
        for rec in self:
            if rec.remaining_amount <= 0.0:
                rec.is_closed = True
            else:
                rec.is_closed = False

    def _search_is_closed(self, operator, value):
        return self._search_closed(operator, value, 'is_closed')

    def _search_closed(self, operator, value, field):
        ids = []
        for order in self.search([]):
            if OPERATORS[operator](order[field], value):
                ids.append(order.id)
        return [('id', 'in', ids)]

    @api.multi
    @api.constrains('correlation_order_line')
    def _check_correlation_order_line(self):
        for rec in self:
            for line in rec.correlation_order_line:
                if line.correlated_amount <= 0:
                    raise ValidationError(_('Please Set Required Amount for line %s' % line.budget_line_id.general_budget_id.name))
                if line.correlated_amount > line.budget_line_id.remaining_without_correlation:
                    raise ValidationError(_(
                        'There is not enough budget to correlate for line %s' % line.budget_line_id.general_budget_id.name))

    # @api.multi
    # def _update_budget_line(self, budget_line_id, correlated_amount):
    #     correlation_amount = budget_line_id.correlated_amount + correlated_amount
    #     budget_line_id.write({'correlated_amount': correlation_amount})

    @api.multi
    def button_confirm(self):
        for rec in self:
            rec._check_correlation_order_line()
            code = self.env['ir.sequence'].with_context(ir_sequence_date=rec.date).next_by_code('correlation.order') or '/'
            rec.write({'code': code,'state': 'confirm'})
            account_users = self.env['res.users'].search([('groups_id', '=',
                                                            self.env.ref('account.group_account_user').id),
                                                           ('groups_id', 'not in', (
                                                               self.env.ref('slnee_security.group_service_manager').id,
                                                               self.env.ref('slnee_security.group_gm').id)),
                                                           ('company_id', '=', rec.company_id.id)])
            partner_ids = []
            account_users and partner_ids.extend(account_users.mapped('partner_id').ids)
            rec.message_post(body=_('Please set your approval on %s ') % rec.name, partner_ids=partner_ids)

    @api.multi
    def button_approve(self):
        for rec in self:
            rec._check_correlation_order_line()
            rec.write({'state': 'approve'})

    @api.multi
    def button_refuse(self):
        for rec in self:
            rec._check_correlation_order_line()
            rec.write({'state': 'refuse'})
    @api.multi
    def button_redraft(self):
        self.write({'state': 'draft'})

    @api.multi
    def button_cancel(self):
        for rec in self:
            if rec.payment_order_ids and rec.payment_order_ids.filtered(lambda x: x.state not in ['draft','cancelled']):
                raise ValidationError(_('You can not cancel Correlation order before canceling Payment Order'))
            rec.write({'state': 'cancel'})

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can not delete record"))
        return super(CorrelationOrder, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        name = _('Encumbrance Order')
        for rec in self:
            if rec.code and rec.name:
                name = rec.code + '-' + rec.name
            result.append((rec.id, name))
        return result


class CorrelationOrderLine(models.Model):
    _name = 'correlation.order.line'
    _description = 'Encumbrance Order Lines'
    name = fields.Char(string='Description')
    budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Line')
    budget_id = fields.Many2one('crossovered.budget', string='Budget Name')
    section_id = fields.Many2one('crossovered.budget.lines.sections', string='Section')
    required_amount = fields.Float(string='Required Amount')
    remaining_amount_without_correlation = fields.Float(string="Available Amount", related='budget_line_id.remaining_without_correlation', store=True)
    correlated_amount = fields.Float(string='Encumbrance Amount')
    # todo compute remaining amount based on payment orders
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_amount')
    is_released = fields.Boolean(string='Is Released?')
    order_id = fields.Many2one('correlation.order', string='Encumbrance Order')
    is_closed = fields.Boolean(string='Is Closed', compute='_compute_amount', search='_search_is_closed')
    state = fields.Selection([('draft', _('Draft')),
                              ('confirm', _('Confirmed')),
                              ('approve', _('Approved')),
                              ('refuse', _('Refused')),
                              ('cancel', _('Cancelled'))], related='order_id.state', default='draft')
    partner_id = fields.Many2one('res.partner' ,related='order_id.partner_id')


    def _search_is_closed(self, operator, value):
        return self._search_closed(operator, value, 'is_closed')


    def _search_closed(self, operator, value, field):
        ids = []
        for order in self.search([]):
            if OPERATORS[operator](order[field], value):
                ids.append(order.id)
        return [('id', 'in', ids)]

    @api.multi
    @api.depends()
    def _compute_amount(self):
        for rec in self:
            rec.remaining_amount = rec.correlated_amount
            if rec.is_released:
                rec.remaining_amount = 0.0
            if rec.remaining_amount<=0.0:
                rec.is_closed =True
            else:
                rec.is_closed = False

    @api.multi
    def button_release(self):
        for rec in self:
            if rec.remaining_amount:
                rec.correlated_amount -= rec.remaining_amount
                rec.is_released = True


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    correlation_line_ids = fields.One2many('correlation.order.line', 'budget_line_id', string='Correlation Lines')
    correlated_amount = fields.Float(string="Correlated Amount", compute='_compute_correlated_amount')


    @api.depends('correlation_line_ids')
    def _compute_correlated_amount(self):
        for rec in self:
            correlated_amount = sum([line.correlated_amount for line in rec.correlation_line_ids if line.state =='approve'])
            rec.correlated_amount = correlated_amount


