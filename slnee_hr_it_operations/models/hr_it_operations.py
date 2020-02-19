# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    it_operations_id = fields.Many2one('hr.it.operations', 'IT Operations')

#===============================================================================
# class stock_partial_picking(models.TransientModel):
#     _inherit = "stock.partial.picking"
#
#     def do_partial(self, cr, uid, ids, context=None):
#         assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
#         stock_picking = self.pool.get('stock.picking')
#         stock_move = self.pool.get('stock.move')
#         uom_obj = self.pool.get('product.uom')
#         partial = self.browse(cr, uid, ids[0], context=context)
#         partial_data = {
#             'delivery_date' : partial.date
#         }
#         picking_type = partial.picking_id.type
#         for wizard_line in partial.move_ids:
#             line_uom = wizard_line.product_uom
#             move_id = wizard_line.move_id.id
#
#             Quantiny must be Positive
#             if wizard_line.quantity < 0:
#                 raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))
#
#             Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
#             qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, line_uom.id)
#
#             if line_uom.factor and line_uom.factor <> 0:
#                 if float_compare(qty_in_line_uom, wizard_line.quantity, precision_rounding=line_uom.rounding) != 0:
#                     raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only roundings of "%s %s" is accepted by the Unit of Measure.') % (wizard_line.quantity, line_uom.name, line_uom.rounding, line_uom.name))
#             if move_id:
#                 Check rounding Quantity.ex.
#                 picking: 1kg, uom kg rounding = 0.01 (rounding to 10g),
#                 partial delivery: 253g
#                 > result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
#                 initial_uom = wizard_line.move_id.product_uom
#                 Compute the quantity for respective wizard_line in the initial uom
#                 qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, initial_uom.id)
#                 without_rounding_qty = (wizard_line.quantity / line_uom.factor) * initial_uom.factor
#                 if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
#                     raise osv.except_osv(_('Warning!'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only roundings of "%s %s" is accepted by the uom.') % (wizard_line.quantity, line_uom.name, wizard_line.move_id.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
#             else:
#                 seq_obj_name =  'stock.picking.' + picking_type
#                 move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
#                                                     'product_id': wizard_line.product_id.id,
#                                                     'product_qty': wizard_line.quantity,
#                                                     'product_uom': wizard_line.product_uom.id,
#                                                     'prodlot_id': wizard_line.prodlot_id.id,
#                                                     'location_id' : wizard_line.location_id.id,
#                                                     'location_dest_id' : wizard_line.location_dest_id.id,
#                                                     'picking_id': partial.picking_id.id
#                                                     },context=context)
#                 stock_move.action_confirm(cr, uid, [move_id], context)
#             partial_data['move%s' % (move_id)] = {
#                 'product_id': wizard_line.product_id.id,
#                 'product_qty': wizard_line.quantity,
#                 'product_uom': wizard_line.product_uom.id,
#                 'prodlot_id': wizard_line.prodlot_id.id,
#             }
#             if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
#                 partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
#                                                                   product_currency=wizard_line.currency.id)
#         data = stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
#         stock_obj = self.pool.get('stock.picking.out')
#         id =[data[id]['delivered_picking'] for id in data]
#         if context.get('active_id',False):
#             if stock_obj.browse(cr, uid, context.get('active_id'), context=context).it_operations_id:
#                 vals={'it_operations_id':stock_obj.browse(cr, uid, context.get('active_id'), context=context).it_operations_id.id}
#                 return_val = stock_obj.write(cr, uid, id[0],vals,context=context)
#
#         return {'type': 'ir.actions.act_window_close'}
#===============================================================================


class HRITOperations(models.Model):

    @api.depends('expense_total', 'company_contribution')
    def _employee_contribution(self):
        '''
            Calculate Employee contribution
            Contribution = Total Expense - Company Contribution
        '''
        for contribution in self:
            contribution.emp_contribution = contribution.expense_total - contribution.company_contribution or 0.0

    _name = 'hr.it.operations'
    _description = 'HR IT Operations'
    _inherit = ['mail.thread']

    name = fields.Char('Name')
    type = fields.Selection([('software', 'Software'), ('hardware', 'Hardware')], string='Request For', required=True, default='software')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    is_damage = fields.Boolean('Damage')
    expense_total = fields.Float('Total Expense', digits=dp.get_precision('Account'))
    company_contribution = fields.Float('Company Contribution', digits=dp.get_precision('Account'))
    emp_contribution = fields.Float(compute=_employee_contribution, string='Employee Contribution', digits=dp.get_precision('Account'))
    expense_id = fields.Many2one('hr.expense', 'Expense')
    expense_note = fields.Text('Expense Note')
    job_id = fields.Many2one('hr.job', 'Job Position', readonly=True)
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    description = fields.Text('Description', required=True)
    picking_ids = fields.One2many('stock.picking', 'it_operations_id', 'Picking List', readonly=True, help="This is the list of incoming shipments that have been generated for this purchase order.")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Waiting for Approval'),
                              ('validate', 'Validated'),
                              ('approve', 'Approved'),
                              ('refuse', 'Refused'), ], track_visibility='onchange', string="Status", default='draft')
    validated_date = fields.Datetime(string='Validated on', readonly=True, copy=False)
    validated_by = fields.Many2one('res.users', 'Validated by', readonly=True, copy=False)
    approved_date = fields.Datetime(string='Approved on', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    refused_by = fields.Many2one('res.users', 'Refused by', readonly=True, copy=False)
    refused_date = fields.Datetime(string='Refused on', readonly=True, copy=False)

    @api.multi
    def unlink(self):
        '''
            Remove a record
        '''
        for operation in self:
            if operation.state in ['confirm', 'validate', 'approve', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (operation.state))
        return super(HRITOperations, self).unlink()

    @api.multi
    def name_get(self):
        '''
            Return a name with Concatinate Operation type and creation date
            for eg. Name + Operation Type + Creation Date
        '''
        res = []
        for operation in self:
            date = datetime.strptime(operation.create_date, '%Y-%m-%d %H:%M:%S')
            create_date = date.strftime('%Y-%m-%d')
            name = ' - '.join([operation.employee_id.name or '', operation.type or '',
                               create_date or ''])
            res.append((operation.id, name))
        return res

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        '''
            Set details of Department, Job and Code of Employee based on select Employee.
        '''
        self.department_id = False
        self.job_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id or False
            self.job_id = self.employee_id.job_id.id or False

    @api.model
    def create(self, vals):
        '''
            Create a new record
        '''
        if vals.get('employee_id', False):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id or False,
                         'job_id': employee.job_id.id or False, })
        return super(HRITOperations, self).create(vals)

    @api.multi
    def write(self, vals):
        '''
            Update an existing record
        '''
        if vals.get('employee_id', False):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'job_id': employee.job_id.id or False,
                         'department_id': employee.department_id.id or False})
        return super(HRITOperations, self).write(vals)

    @api.multi
    def validate_it_operations(self):
        '''
            Validate IT Operation
        '''
        self.ensure_one()
        today = datetime.today()
        helpdesk_groups_config_obj = self.env['hr.groups.configuration']
        helpdesk_groups_config_ids = helpdesk_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id or False), ('helpdesk_ids', '!=', None)])
        user_ids = helpdesk_groups_config_ids and [employee.user_id.id for employee in helpdesk_groups_config_ids.helpdesk_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids)
        self.state = 'validate'
        self.validated_by = self.env.uid
        self.validated_date = today
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Request Validated.'))

    @api.multi
    def confirm_it_operations(self):
        '''
            Confirm IT Operation
        '''
        self.ensure_one()
        self.state = 'confirm'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Request Confirmed.'))

    @api.multi
    def approve_it_operations(self):
        # TO DO
        '''
            Approve IT Operation
        '''
        self.ensure_one()
        today = fields.Datetime.now()
        if self.employee_id.user_id.partner_id:
            picking_type_ids = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
            if picking_type_ids:
                ctx = self._context.copy()
                ctx.update({'default_picking_type_id': picking_type_ids[0].id})
                location_dest_id = self.env['stock.picking.type'].browse(ctx.get('default_picking_type_id')).default_location_dest_id
                if location_dest_id:
                    stock_id = self.env['stock.picking'].with_context(ctx).create({'partner_id': self.employee_id.user_id.partner_id.id,
                                    'location_dest_id': location_dest_id.id, 'picking_type_id': picking_type_ids[0].id})
                    self.picking_ids = [(6, 0, [stock_id.id])]
            self.state = 'approve'
            self.approved_by = self.env.uid
            self.approved_date = today
            self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Request Approved.'))
        else:
            raise UserError(_('Related user of employee must have partner.'))

    @api.multi
    def generate_expense(self):
        '''
            Calculate expenses of Company Contribution and Total Expenses
            Return expense view.
        '''
        if self.expense_total <= 0 or self.company_contribution > self.expense_total:
            raise UserError(_('Expense Total should be either greater then 0 or company contribution should not be more that total expense'))
        product_id = self.env.ref('slnee_hr_it_operations.it_product')
        expense_data = {
            'employee_id': self.employee_id.id or False,
            'product_id': product_id.id,
            'unit_amount': self.expense_total,
            'date': datetime.today().date(),
            'quantity': 1,
            'name': 'IT Operation - ' + self.name_get()[0][1],
            'source': 'IT Operation - ' + self.name_get()[0][1],
            'company_contribution': self.company_contribution,
            'description': self.expense_note,
        }
        expense_id = self.env['hr.expense'].create(expense_data)
        self.expense_id = expense_id
        return self.redirect_to_expense(expense_id.id)

    @api.multi
    def view_expense(self):
        '''
            Open an existing / linkage expense with current record.
        '''
        return self.redirect_to_expense(self.expense_id.id)

    @api.multi
    def redirect_to_expense(self, expense_id):
        '''
            Redirect on view of expense
        '''
        view = self.env.ref('hr_expense.hr_expense_form_view')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses'),
            'res_model': 'hr.expense',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': expense_id,
            'context': self.env.context,
        }

    @api.multi
    def set_to_draft(self):
        '''
            IT Operation Reset In inital state.
        '''
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Request Created.'))

    @api.multi
    def refuse_it_operations(self):
        '''
            IT Operation is refusing / Cancel
        '''
        self.ensure_one()
        self.state = 'refuse'
        self.refused_by = self.env.uid
        self.refused_date = fields.Datetime.now()
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Request Refused.'))

    @api.multi
    def view_delivery_order(self):
        '''
            Open a Delivery Order which is linked with record.
        '''
        mod_obj = self.env['ir.model.data']
        res = mod_obj.get_object_reference('stock', 'vpicktree')
        pick_ids = [picking.id for picking in self.picking_ids]
        result = {
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'stock.picking',
            # 'target': 'new',
            'domain': '[]',
            'views': [(res and res[1] or False, 'tree')],
        }
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('stock', 'view_picking_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result
