
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BudgetTransfer(models.Model):
    _name = 'budget.transfer'
    _description ='Budget Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    """
    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('slnee_budget_transfer.use_percentage_while_transfer'):
            return True
        return False

    def _default_percentage_to_approve_source_avil_amount(self):
        if self.env['ir.config_parameter'].sudo().get_param('slnee_budget_transfer.use_percentage_while_transfer'):
            return self.env.user.company_id.percentage_to_approve_source_avil_amount
        return False

    def _default_percentage_to_check_trans_amount_to_planned(self):
        if self.env['ir.config_parameter'].sudo().get_param('slnee_budget_transfer.use_percentage_while_transfer'):
            return self.env.user.company_id.percentage_to_check_trans_amount_to_planned
        return False

    """

    #use_transfer_conditions = fields.Boolean(readonly=True, copy=False, default=_default_validity_date)
    #percentage_to_approve_source_avil_amount = fields.Float(default=_default_percentage_to_approve_source_avil_amount)
    #percentage_to_check_trans_amount_to_planned = fields.Float(default=_default_percentage_to_check_trans_amount_to_planned)
    date = fields.Date(string='Date', default=fields.Date.today())
    name = fields.Char(string='Name', default='/',copy=False)
    #operation_type = fields.Selection([('same_section',_('Transfer In Same Section')),('diff_section',_('Transfer Between Different Section'))], string='Operation Type')
    from_section_id = fields.Many2one('crossovered.budget.lines.sections', string='From Section Name', required=True)
    to_section_id = fields.Many2one('crossovered.budget.lines.sections', string='To Section Name', required=True)
    from_budget_id = fields.Many2one('crossovered.budget', string='From Budget', required=True)
    to_budget_id = fields.Many2one('crossovered.budget', string='To Budget', required=True)

    from_budget_line_id = fields.Many2one('crossovered.budget.lines', string='From Budget Line')
    #from_budget_line_planned_amount = fields.Float(string='Confirmed Amount')
    #from_budget_avail_amount = fields.Float(string='Available Amount')
    #from_budget_line_avil_amount_after = fields.Float(string='Available Amount After Transfer')

    to_budget_line_id = fields.Many2one('crossovered.budget.lines', string='TO Budget Line')
    amount = fields.Float(string='Transfer Amount')
    #to_budget_line_planned_amount = fields.Float(string='Confirmed Amount')
    #to_budget_line_avil_amount_before = fields.Float(string='Available Amount Before Transfer')
    #to_budget_line_avil_amount_after = fields.Float(string='Available Amount After Transfer', compute='_get_avail_amount')

    state = fields.Selection([('draft',_('Draft')),
                              ('confirm',_('Confirmed')),
                              ('approve',_('Approved')),
                              ('reverse',_('Reversed')),
                              ('refuse',_('Refused')),
                              ('cancel',_('Cancelled')),
                              ], string='State', default='draft')
    notes = fields.Text(string='Notes')
    #readonly_state = fields.Boolean()
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    reason = fields.Text(string='Transfer Reasons')

    """
    @api.onchange('operation_type','from_section_id')
    def onchange_section(self):
        if self.operation_type == 'same_section' and self.from_section_id:
            self.to_section_id = self.from_section_id.id
    """
    """
    @api.onchange('to_budget_line_id', 'from_budget_line_id')
    def onchange_budget_lines(self):
        if self.from_budget_line_id:
            self.from_budget_line_planned_amount = abs(self.from_budget_line_id.planned_amount)
            self.from_budget_avail_amount = abs(self.from_budget_line_id.remaining_without_correlation)
        if self.to_budget_line_id:
            self.to_budget_line_planned_amount = abs(self.to_budget_line_id.planned_amount)
            self.to_budget_line_avil_amount_before = abs(self.to_budget_line_id.remaining_without_correlation)
    """
    @api.constrains('from_budget_line_id', 'to_budget_line_id')
    def _check_budget_line(self):
        if self.to_budget_line_id and self.from_budget_line_id and self.from_budget_line_id.id == self.to_budget_line_id.id:
            raise ValidationError(_('Two budget line can not be same'))
    """
    @api.constrains('amount_required')
    def _check_amount_required(self):
        if self.amount_required > abs(self.from_budget_avail_amount):
            raise ValidationError(_('Amount Required can not be greater than available amount in %s'%self.from_budget_line_id.name))
        if self.use_transfer_conditions and self.percentage_to_approve_source_avil_amount:
            percentage = self.percentage_to_approve_source_avil_amount / 100.0
            if self.transferred_amount > self.from_budget_avail_amount * percentage:
                raise ValidationError(_(
                    'Please check Required amount should not be greater than From budget line available amount by %f' % percentage))

        if self.use_transfer_conditions and self.percentage_to_approve_dest_avil_amount:
            percentage = self.percentage_to_approve_dest_avil_amount / 100.0
            if self.transferred_amount > self.to_budget_line_planned_amount * percentage:
                raise ValidationError(_(
                    'Required Amount can not greater or equal to To Budget Line Planned Amount by %f' %percentage))
    @api.multi
    def update_budget_line(self):
        # from_budget_line_planned_amount =abs(self.from_budget_line_planned_amount) - self.amount_required
        # to_budget_line_planned_amount = abs(self.to_budget_line_planned_amount) + self.amount_required
        # if self.from_budget_line_id.planned_amount < 0:
        #     from_budget_line_planned_amount = from_budget_line_planned_amount *-1
        # if self.to_budget_line_id.planned_amount<0:
        #     to_budget_line_planned_amount = to_budget_line_planned_amount *-1
        self.from_budget_line_id.sudo().write({'amount_transfer_out': self.from_budget_line_id.amount_transfer_out+self.amount_required})
        self.to_budget_line_id.sudo().write({'amount_transfer_in': self.to_budget_line_id.amount_transfer_in+self.amount_required})

    @api.multi
    @api.depends('to_budget_line_avil_amount_before', 'amount_required')
    def _get_avail_amount(self):
        for rec in self:
            rec.to_budget_line_avil_amount_after = rec.to_budget_line_avil_amount_before + rec.amount_required
    """

    @api.multi
    def reverse_transfer(self):
        # from_budget_line_planned_amount =abs(self.from_budget_line_planned_amount) - self.amount_required
        # to_budget_line_planned_amount = abs(self.to_budget_line_planned_amount) + self.amount_required
        # if self.from_budget_line_id.planned_amount < 0:
        #     from_budget_line_planned_amount = from_budget_line_planned_amount *-1
        # if self.to_budget_line_id.planned_amount<0:
        #     to_budget_line_planned_amount = to_budget_line_planned_amount *-1
        if self.to_budget_line_id.funds_check(self.amount):
            self.from_budget_line_id.sudo().write(
                {'amount_transfer_out': self.from_budget_line_id.amount_transfer_out - self.amount})
            self.to_budget_line_id.sudo().write(
                {'amount_transfer_in': self.to_budget_line_id.amount_transfer_in - self.amount})

    @api.multi
    def update_budget_line(self):
        # from_budget_line_planned_amount =abs(self.from_budget_line_planned_amount) - self.amount_required
        # to_budget_line_planned_amount = abs(self.to_budget_line_planned_amount) + self.amount_required
        # if self.from_budget_line_id.planned_amount < 0:
        #     from_budget_line_planned_amount = from_budget_line_planned_amount *-1
        # if self.to_budget_line_id.planned_amount<0:
        #     to_budget_line_planned_amount = to_budget_line_planned_amount *-1
        if self.from_budget_line_id.funds_check(self.amount):
            self.from_budget_line_id.sudo().write(
                {'amount_transfer_out': self.from_budget_line_id.amount_transfer_out + self.amount})
            self.to_budget_line_id.sudo().write(
                {'amount_transfer_in': self.to_budget_line_id.amount_transfer_in + self.amount})

    @api.multi
    def action_confirm(self):
        for rec in self:
            if rec.from_budget_line_id.funds_check(self.amount):
                name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.date).next_by_code('budget.transfer') or '/'
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
        self.reverse_transfer()
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
        return super(BudgetTransfer, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        name = _('Budget Transfer')
        for rec in self:
            if rec.name:
                name = rec.name + '-' + name
            result.append((rec.id, name))
        return result


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    amount_transfer_out = fields.Float(string='Transfer Out', readonly=True, copy=False)
    amount_transfer_in = fields.Float(string='Transfer In', readonly=True, copy=False)
    out_transfer_ids = fields.One2many('budget.transfer', 'from_budget_line_id', string='Transfered-Out Operations')
    in_transfer_ids = fields.One2many('budget.transfer', 'to_budget_line_id', string='Transfered-In Operations')

