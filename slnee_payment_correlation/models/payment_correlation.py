# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError


class PaymentCorrelationLine(models.Model):
    _name = 'payment.correlation.line'

    correlation_order_id = fields.Many2one('correlation.order', string='Encumbrance Order')
    correlation_line_id = fields.Many2one('correlation.order.line', string='Encumbrance Budget Line')
    budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Line')
    available_amount = fields.Float(string='Available Amount')
    required_amount = fields.Float(string='Required Amount')
    expense_account_id = fields.Many2one('account.account', string='Expense Account')
    payment_id = fields.Many2one('account.payment', string='Payment Order')

    @api.one
    @api.constrains('required_amount')
    def check_required_amount(self):
        if self.required_amount > self.available_amount:
            raise ValidationError(_("The required amount can not exceed the available quantity !!"))

    @api.onchange('correlation_line_id')
    def _onchange_correlation_line_id(self):
        self.budget_line_id =False
        self.correlation_order_id =False
        self.available_amount =False
        if self.correlation_line_id:
            self.budget_line_id = self.correlation_line_id.budget_line_id.id
            self.correlation_order_id = self.correlation_line_id.order_id.id
            self.available_amount = self.correlation_line_id.remaining_amount

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    using_correlation = fields.Selection([('yes',_('Yes')),('no',_('NO'))], string='With Encumbrance', default='yes')
    payment_line_ids = fields.One2many('payment.correlation.line', 'payment_id', string='Payment Encumbrance Lines')
    correlation_order_id = fields.Many2one('correlation.order', string='Encumbrance Order')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor'), ('employee', 'Employee')])
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),('approve', 'Approve'),('validate', 'Validate'),('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
                              ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")

    @api.onchange('using_correlation', 'correlation_order_id')
    def _onchange_correlation(self):
        self.payment_line_ids = False
        if self.using_correlation == 'no':
            self.correlation_order_id =False
            self.payment_line_ids =False
        if self.correlation_order_id:
            self.payment_line_ids =False


    

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            # Set default partner type for the payment type

            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
            else:
                self.partner_type = False
            if self._context.get('is_for_employee', False) and self.payment_type=='outbound':
                self.partner_type = 'employee'
            else:
                self.partner_type = False
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        journal_types.update(['bank', 'cash'])
        res['domain']['journal_id'] = jrnl_filters['domain'] + [('type', 'in', list(journal_types))]
        return res


    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'validate':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                    if rec.partner_type == 'employee':
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.employee'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    def _check_constraints(self,record):
        if record.using_correlation == 'yes' and not record.payment_line_ids:
            ValidationError(_("Kindly Enter payment line to specify the Encumbrance Order line and the required amount ."))

    @api.multi
    def confirm(self):
        for record in self:
            if record.using_correlation == 'yes' and not record.payment_line_ids:
                raise ValidationError(_("Kindly Enter payment line to specify the correlation Order line and the required amount ."))
            service_users = self.env['res.users'].search([('groups_id', '=',
                                                           self.env.ref('slnee_security.group_service_manager').id),
                                                          ('company_id', '=', record.company_id.id)])
            partner_ids = [partner.id for partner in service_users.mapped('partner_id')]
            record.message_post(body=_('Please Approve Payment Order for %s') % record.partner_id.name,
                                partner_ids=partner_ids)
            record.state ='confirm'

    @api.multi
    def approve(self):
        for record in self:
            if not record.company_id.payment_order_amount_limit:
                raise ValidationError(_('Please set Payment Order limit amount for approavl through system settings, contact administrator'))
            if record.amount >= record.company_id.payment_order_amount_limit:
                gm_user = self.env['res.users'].search([('groups_id', '=',
                                                               self.env.ref('slnee_security.group_gm').id),
                                                              ('company_id', '=', record.company_id.id)])
                partner_ids = [partner.id for partner in gm_user.mapped('partner_id')]
                record.message_post(body=_('Please Approve Payment Order for %s') % record.partner_id.name,
                                    partner_ids=partner_ids)
                record.state ='approve'
            else:
                account_users = self.env['res.users'].search([('groups_id', '=',
                                                               self.env.ref('account.group_account_user').id),
                                                              ('groups_id', 'not in', (
                                                                  self.env.ref('slnee_security.group_service_manager').id,
                                                                  self.env.ref('slnee_security.group_gm').id)),
                                                              ('company_id', '=', record.company_id.id)])
                account_partner_ids = [partner.id for partner in account_users.mapped('partner_id')]

                record.message_post(body=_('Payment Order for %s had been Approved') % record.partner_id.name,
                                    partner_ids=account_partner_ids)
                record.state ='validate'
    @api.multi
    def validate(self):
        for record in self:
            account_users = self.env['res.users'].search([('groups_id', '=',
                                                           self.env.ref('account.group_account_user').id),
                                                          ('groups_id', 'not in', (
                                                              self.env.ref('slnee_security.group_service_manager').id,
                                                              self.env.ref('slnee_security.group_gm').id)),
                                                          ('company_id', '=', record.company_id.id)])
            account_partner_ids = [partner.id for partner in account_users.mapped('partner_id')]

            record.message_post(body=_('Payment Order for %s had been Approved') % record.partner_id.name,
                                partner_ids=account_partner_ids)
            record.state = 'validate'



class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    payment_line_ids = fields.One2many('payment.correlation.line', 'budget_line_id', string='Payment Lines')
    consumed_amount = fields.Float(string='Consumed Amount', compute='_compute_consumed_amount')


    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.general_budget_id.name
            result.append((record.id, name))
        return result

    @api.depends('correlation_line_ids')
    def _compute_consumed_amount(self):
        for rec in self:
            rec.consumed_amount = sum(
                [line.required_amount for line in rec.payment_line_ids if line.payment_id.state in ['posted','reconciled']])

class CorrelationOrder(models.Model):
    _inherit='correlation.order'

    payment_order_ids = fields.One2many('account.payment', 'correlation_order_id', string='Payment Orders')


class CorrelationOrderLine(models.Model):
    _inherit = 'correlation.order.line'

    payment_line_ids = fields.One2many('payment.correlation.line', 'correlation_line_id', string='Payment Order Lines')
    consumed_amount = fields.Float(string='Consumed Amount', compute='_compute_amount')

    @api.multi
    @api.depends('payment_line_ids')
    def _compute_amount(self):
        for rec in self:
            consumed_amount = sum(line.required_amount for line in rec.payment_line_ids if
                                  line.payment_id.state not in ['draft', 'cancelled'] and line.correlation_line_id.id == rec.id)
            rec.consumed_amount = consumed_amount
            rec.remaining_amount = rec.correlated_amount - consumed_amount
            if rec.is_released:
                rec.remaining_amount = 0.0
            if rec.is_released or rec.remaining_amount <= 0.0:
                rec.is_closed =True
            else:
                rec.is_closed = False

