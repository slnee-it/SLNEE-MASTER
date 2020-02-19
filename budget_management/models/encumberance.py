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

class EncumbOrder(models.Model):
    _name = 'encumb.order'
    _description = 'Encumbrance Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    type = fields.Selection([('po','Purchase Order'),('bill','Vendor Bill')],string="Type")
    code = fields.Char(string='Code', default='/',copy=False)
    date = fields.Date(string='Date', default=fields.Date.today(), track_visibility='onchange')
    name = fields.Char(string='Description', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner',domain=[('supplier','=',True)], string='Beneficiary Name', track_visibility='onchange')
    encumbered_amount = fields.Monetary(string='Encumbrance Amount', currency_field='currency_company_id',
                                            readonly=True, compute='_compute_consume',
                                            help="Total Encumberance amount", track_visibility='onchange')
    released_amount = fields.Monetary(string='Released Amount', currency_field='currency_company_id',
                                        readonly=True, compute='_compute_consume',
                                        help="Total Released amount", track_visibility='onchange')
    reserved_amount = fields.Monetary(string='Reserved Amount', currency_field='currency_company_id',
                                        readonly=True, compute='_compute_consume',
                                        help="Total Reserved amount", track_visibility='onchange')
    remaining_amount = fields.Monetary(string='Remaining Amount', currency_field='currency_company_id',
                                        readonly=True, compute='_compute_consume',
                                        help="Total Remaining amount", track_visibility='onchange')

    consumed_amount = fields.Float(string='Consumed Amount',compute='_compute_consume')
    origin = fields.Char(string='Origin')
    encumb_line_ids = fields.One2many('encumb.order.line', 'order_id', string='Encumbrance Order Details')
    invoice_ids = fields.One2many('account.invoice', 'encumb_id', string='Vendor Bills',readonly=True,copy=False)
    currency_company_id = fields.Many2one('res.currency', related='company_id.currency_id',string='Company Currency',readonly=True)

    state = fields.Selection([('draft', _('Draft')),
                              ('confirm', _('Confirmed')),
                              ('approve', _('Approved')),
                              ('done', _('Done')),
                              ('reverse', _('Reversed')),
                              ('refuse', _('Refused')),
                              ('cancel', _('Cancelled')),
                              ], string='State', track_visibility='onchange',default='draft')
    notes = fields.Text(string='Notes', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id, track_visibility='onchange')

    @api.multi
    @api.depends('encumb_line_ids.encumbered_amount', 'encumb_line_ids.remaining_amount','encumb_line_ids.released_amount', 'encumb_line_ids.reserved_amount')
    def _compute_consume(self):
        for rec in self:
            rec.consumed_amount = sum(col.released_amount for col in rec.encumb_line_ids)
            rec.encumbered_amount = sum(col.encumbered_amount for col in rec.encumb_line_ids)
            rec.released_amount = sum(col.released_amount for col in rec.encumb_line_ids)
            rec.reserved_amount = sum(col.reserved_amount for col in rec.encumb_line_ids)
            rec.remaining_amount = sum(col.remaining_amount for col in rec.encumb_line_ids)

    @api.model
    def release_inv_encumb(self,invoice):
        """
        This function release the invoice amount from encumberance order
        :param invoice:
        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('budget_management.allow_encumber_and_funds_check'):
            count = 0
            for line in invoice.invoice_line_ids:
                deduct_amount = line.price_subtotal_signed

                for encumb_line in invoice.encumb_id.encumb_line_ids:
                    count += 1
                    if line.account_analytic_id.id == encumb_line.analytic_account_id.id:
                        reserved_amount = encumb_line.reserved_amount
                        released_amount = encumb_line.released_amount
                        if reserved_amount >= deduct_amount:
                            reserved_amount = reserved_amount - deduct_amount
                            released_amount = released_amount + deduct_amount
                            encumb_line.reserved_amount = reserved_amount
                            encumb_line.released_amount = released_amount
                            #raise ValidationError(_(str(encumb_line.reserved_amount) + "               " + str(encumb_line.released_amount)))
                            #encumb_line.write({'reserved_amount':reserved_amount ,'released_amount':released_amount})
                        else:
                            raise ValidationError(_("There"))
                            amount = reserved_amount
                            reserved_amount = 0
                            released_amount = released_amount + amount
                            raise ValidationError(_(str(reserved_amount) + "               " + str(released_amount)))
                            encumb_line.reserved_amount = reserved_amount
                            encumb_line.released_amount = released_amount
                            deduct_amount = deduct_amount - amount
                            #encumb_line.write({'reserved_amount': reserved_amount, 'released_amount': released_amount})
            #raise ValidationError(_(str(count)))
            #if invoice.encumb_id.type == 'bill' and self.env['ir.config_parameter'].sudo().get_param('budget_management.module_bills_encumberance'):
                #invoice.encumb_id.write({'origin':invoice.number })

    @api.model
    def get_account(self,product):
        """
        This function return expense account from the product profile or its category
        :return: id
        """
        if product and product.property_account_expense_id:
            return product.property_account_expense_id
        else:
            return product.categ_id.property_account_expense_categ_id

    @api.model
    def check_combination_budget(self, account_id , analytic_account_id,date=fields.Date.today()):
        """
        This function to check whether the combination between account and analytic account do exist in budget
        :return: id
        """
        if account_id and account_id.user_type_id.name == 'Expenses':
            if not account_id:
                raise ValidationError(_(" Please set an account "))
            elif not analytic_account_id:
                raise ValidationError(_("Please set analytic account for line with expense account '%s'")%(account_id.name))
            self.env.cr.execute("""
                                                                    SELECT budget_id
                                                                    FROM account_budget_rel
                                                                    WHERE account_id=%s
                                                                        """,
                                (account_id.id,))
            result = self.env.cr.fetchone() or False
            if not result:
                raise ValidationError(_("The account '%s' is not linked to any budget position")%(account_id.name))

            budget_line_id = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',analytic_account_id.id),('general_budget_id','=',result[0]),('date_from','<',date),('date_to','>',date)],limit=1)
            if not budget_line_id:
                raise ValidationError(_("There is not budget for the combination of the account '%s' and the analytic account '%s'")%(account_id.name,analytic_account_id.name))
            return True

    @api.multi
    def button_confirm(self):
        for rec in self:
            for line in rec.encumb_line_ids:
                if line.budget_line_id.funds_check(line.encumbered_amount):
                    continue
            #rec._check_correlation_order_line()
            code = self.env['ir.sequence'].with_context(ir_sequence_date=rec.date).next_by_code('encumb.order') or '/'
            rec.write({'code': code,'state': 'confirm'})
            account_users = self.env['res.users'].search([('groups_id', '=',
                                                            self.env.ref('account.group_account_user').id),
                                                           ('groups_id', 'in', (
                                                               self.env.ref('budget_management.group_budget_manager').id,
                                                               )),
                                                           ('company_id', '=', rec.company_id.id)])
            partner_ids = []
            account_users and partner_ids.extend(account_users.mapped('partner_id').ids)
            rec.message_post(body=_('Please set your approval on %s ') % rec.name, partner_ids=partner_ids)

    @api.multi
    def button_refuse(self):
        for rec in self:
            # rec._check_correlation_order_line()
            rec.write({'state': 'refuse'})

    @api.multi
    def button_done(self):
        for rec in self:
            # rec._check_correlation_order_line()
            rec.write({'state': 'done'})

    @api.multi
    def button_approve(self):
        for rec in self:
            #rec._check_correlation_order_line()
            rec.write({'state': 'approve'})

    @api.multi
    def button_reverse(self):
        for rec in self:
            #rec._check_correlation_order_line()
            rec.write({'state': 'reverse'})
    @api.multi
    def button_redraft(self):
        self.write({'state': 'draft'})

    @api.multi
    def button_cancel(self):
        for rec in self:
            #if rec.payment_order_ids and rec.payment_order_ids.filtered(lambda x: x.state not in ['draft','cancelled']):
                #raise ValidationError(_('You can not cancel Encumberance order er'))
            rec.write({'state': 'cancel'})

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can not delete record"))
        return super(EncumbOrder, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        name = _('Encumbrance Order')
        for rec in self:
            if rec.code and rec.name:
                name = rec.code + '-' + rec.name
            result.append((rec.id, name))
        return result


class EncumberanceOrderLine(models.Model):
    _name = 'encumb.order.line'
    _description = 'Encumbrance Order Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string='Date', related='order_id.date')
    name = fields.Char(string='Description')
    account_id = fields.Many2one('account.account','Account')
    budget_post_id = fields.Many2one('account.budget.post','Budget Position',required=True)
    budget_line_id = fields.Many2one('crossovered.budget.lines',track_visibility='onchange',string='Budget Line')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic account',required=True)
    encumbered_amount = fields.Float(string='Encumbrance Amount',track_visibility='onchange')
    reserved_amount = fields.Float(string='Reserved Amount',compute='_compute_reserved_amount',default=0)
    released_amount = fields.Float(string='Released Amount',default=0)
    remaining_amount = fields.Float(string='Remaining Amount',compute='_compute_reserved_amount')
    is_released = fields.Boolean(string='Is Released?',default=False)
    order_id = fields.Many2one('encumb.order', string='Encumbrance Order')
    #is_closed = fields.Boolean(string='Is Closed', compute='_compute_amount', search='_search_is_closed')
    state = fields.Selection([('draft', _('Draft')),
                              ('confirm', _('Confirmed')),
                              ('approve', _('Approved')),
                              ('done', _('Done')),
                              ('reverse', _('Reversed')),
                              ('refuse', _('Refused')),
                              ('cancel', _('Cancelled'))], related='order_id.state', default='draft')
    partner_id = fields.Many2one('res.partner' ,related='order_id.partner_id')

    @api.onchange('budget_post_id','analytic_account_id')
    def _onchange_position_or_analytic(self):
        if self.analytic_account_id and self.budget_post_id:
            budget_line_id = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',self.analytic_account_id.id),('date_from','<=',self.date),('date_to','>=',self.date),('general_budget_id','=',self.budget_post_id.id)],limit=1)
            if budget_line_id:
                self.budget_line_id = budget_line_id
            else:
                raise ValidationError(_("Budget Position '%s' and Analytic account '%s' are not linked in the budget")%(self.budget_post_id.name,self.analytic_account_id.name))


    @api.multi
    @api.constrains('budget_post_id', 'analytic_account_id','encumbered_amount')
    def _check_position_and_analytic(self):
        for rec in self:


            budget_line_id = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',rec.analytic_account_id.id),('date_from','<=',rec.order_id.date),('date_to','>=',rec.order_id.date),('general_budget_id','=',rec.budget_post_id.id)],limit=1)
            if not budget_line_id:
                raise ValidationError(_("Budget Position '%s' and Analytic account '%s' are not linked in the budget")%(rec.budget_post_id.name,rec.analytic_account_id.name))
            elif budget_line_id.remain_amount < rec.encumbered_amount:
                raise ValidationError(_("Budget is not enough for lines with budget position '%s' and analytic account '%s'")%(rec.budget_post_id.name,rec.analytic_account_id.name))
            else:
                amount = 0
                for line in rec.order_id.encumb_line_ids:
                    if line.budget_post_id.id == rec.budget_post_id.id and line.analytic_account_id.id == rec.analytic_account_id.id:
                        amount += line.encumbered_amount
                if budget_line_id.remain_amount < amount:
                    raise ValidationError(
                        _("Budget is not enough for lines with budget position '%s' and analytic account '%s'") % (
                        rec.budget_post_id.name, rec.analytic_account_id.name))

    @api.multi
    @api.depends('order_id.invoice_ids','order_id.invoice_ids.state','order_id.invoice_ids.invoice_line_ids.price_subtotal_signed')
    def _compute_reserved_amount(self):
        total = 0
        for rec in self:
            for invoice in rec.order_id.invoice_ids:
                if invoice.state == 'open' or invoice.origin:
                    continue
                else:
                    for line in invoice.invoice_line_ids:
                        if line.account_analytic_id.id == rec.analytic_account_id.id:
                            total += line.price_subtotal_signed
            rec.reserved_amount = total
            rec.remaining_amount = rec.encumbered_amount - rec.reserved_amount - rec.released_amount
            #if not rec.is_released:
                #rec.remaining_amount = rec.encumbered_amount - rec.reserved_amount - rec.released_amount
                #if rec.remaining_amount == 0 and rec.released_amount:
                    #rec.is_released = True
    """
    @api.multi
    @api.depends('encumbered_amount','reserved_amount','released_amount')
    def _compute_amount(self):
        for rec in self:
            if not rec.is_released:
                rec.remaining_amount = rec.encumbered_amount - rec.reserved_amount - rec.released_amount
                if rec.remaining_amount == 0 and rec.released_amount:
                    rec.is_released = True
    """

    @api.model
    def create(self, vals):
        """
        if 'analytic_account_id' in vals:
            analytic_id = vals['analytic_account_id']
            budget_post_id = vals['budget_post_id']
            date = fields.Date.today()
            if 'date' in vals:
                date = vals['date']
            budget_line_id = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',analytic_id),('date_from','<=',date),('date_to','>=',date),('general_budget_id','=',budget_post_id)],limit=1)
            vals.update({'budget_line_id': budget_line_id.id})
        """
        return super(EncumberanceOrderLine, self).create(vals)

    @api.model
    def write(self, vals):
        """
        if 'analytic_account_id' in vals or 'budget_post_id' in vals:
            if 'analytic_account_id' in vals:
                analytic_id = vals['analytic_account_id']
            else:
                analytic_id = self.analytic_account_id.id
            if 'budget_post_id' in vals:
                budget_post_id = vals['budget_post_id']
            else:
                budget_post_id = self.budget_post_id.id
            date = self.date
            budget_line_id = self.env['crossovered.budget.lines'].search(
                [('analytic_account_id', '=', analytic_id), ('date_from', '<=', date), ('date_to', '>=', date),('general_budget_id','=',budget_post_id)],
                limit=1)
            vals.update({'budget_line_id': budget_line_id.id})
        """
        return super(EncumberanceOrderLine, self).write(vals)



class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    encumb_line_ids = fields.One2many('encumb.order.line', 'budget_line_id', string='Encumbered Lines')
    encumbered_amount = fields.Float(string="Encumbered Amount", compute='_compute_encumbered_amount')


    @api.depends('encumb_line_ids','encumb_line_ids.encumbered_amount','encumb_line_ids.released_amount','encumb_line_ids.analytic_account_id','encumb_line_ids.order_id.state')
    def _compute_encumbered_amount(self):
        for rec in self:
            encumbered_amount = sum([(line.encumbered_amount - line.released_amount) for line in rec.encumb_line_ids if line.order_id.state in ['confirm','approve']])
            rec.encumbered_amount = encumbered_amount



