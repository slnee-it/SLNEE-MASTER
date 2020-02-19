# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class GrRequestType(models.Model):
    _name = 'gr.request.type'
    _description = 'GR Request type'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    documents = fields.Text(string='Documents', type="html")
    expense_needed = fields.Boolean(string='Expense Needed')


class GrOperations(models.Model):
    _name = 'gr.operations'
    _order = 'id desc'
    _inherit = ['mail.thread', 'hr.expense.payment']
    _description = 'GR Operations'

    @api.multi
    def _expense_total(self):
        """
            In total expense calculate employee contribution.
        """
        for contribution in self:
            contribution.expense_total = contribution.emp_contribution + contribution.company_contribution

    name = fields.Char('Name')
    type_id = fields.Many2one('gr.request.type', required=True, string='Operation')
    expense_needed = fields.Boolean('Expense Needed')
    documents = fields.Text('List of Documents Required', readonly=True, default="")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    expense_total = fields.Float(compute=_expense_total, string='Total Expense', digits=dp.get_precision('Account'))
    description = fields.Text('Description')
    is_damage = fields.Boolean('Damage')
    total = fields.Float('Total')
    state = fields.Selection([('draft', 'New'),
                              ('confirm', 'Waiting for Approval'),
                              ('inprogress', 'In progress'),
                              ('done', 'Done'),
                              ('refuse', 'Refuse')], string='Status', default='draft', track_visibility='onchange')
    approved_date = fields.Datetime('Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True, copy=False)
    refused_by = fields.Many2one('res.users', string='Refused by', readonly=True, copy=False)
    refused_date = fields.Datetime('Refused on', readonly=True, copy=False)
    client_name = fields.Char('Client Name', size=50)
    project_name = fields.Char('Project Name', size=50)
    handled_by = fields.Many2one('hr.employee', string="Handled by")
    expense_ids = fields.Many2many('hr.expense', string="Expenses", copy=False)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'slnee_hr_gr_operation_request.mt_gr_operations_new'
        elif 'state' in init_values and self.state == 'confirm':
            return 'slnee_hr_gr_operation_request.mt_gr_operations_confirm'
        elif 'state' in init_values and self.state == 'done':
            return 'slnee_hr_gr_operation_request.mt_gr_operations_done'
        elif 'state' in init_values and self.state == 'refuse':
            return 'slnee_hr_gr_operation_request.mt_gr_operations_refuse'
        return super(GrOperations, self)._track_subtype(init_values)

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for objects in self:
            if objects.state in ['confirm', 'inprogress', 'done', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(GrOperations, self).unlink()

    @api.multi
    @api.depends('employee_id', 'type_id')
    def name_get(self):
        """
            to use retrieving the name, combination of `employee name & operation type name`
        """
        result = []
        for operation in self:
            name = ''.join([operation.employee_id.name or '', ' - ', operation.type_id.name or ''])
            result.append((operation.id, name))
        return result

    @api.model
    def create(self, values):
        """
            Create new record
            :param values: current record fields data
            :return: Newly created record ID
        """
        partner = []
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id})
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
            if employee.parent_id and employee.parent_id.user_id:
                partner.append(employee.parent_id.user_id.partner_id.id)
        if values.get('type_id'):
            types = self.env['gr.request.type'].browse(values['type_id'])
            values.update({'documents': types.documents})
        res = super(GrOperations, self).create(values)
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        if partner:
            res.message_subscribe(partner_ids=partner)
        return res

    @api.multi
    def write(self, values):
        """
            Update an existing record
            :param values: current record fields data
            :return: updated record ID
        """
        partner = []
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id})
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
            if employee.parent_id:
                partner.append(employee.parent_id.user_id.partner_id.id)
        if values.get('type_id'):
            types = self.env['gr.request.type'].browse(values['type_id'])
            values.update({'documents': types.documents})
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(GrOperations, self).write(values)

    @api.multi
    def submit_gr_operations(self):
        """
            sent the status of generating GR operation request in Confirm state
        """
        self.ensure_one()
        gr_groups_config_obj = self.env['hr.groups.configuration']
        gr_groups_config_ids = gr_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id), ('gr_ids', '!=', False)])
        user_ids = gr_groups_config_ids and [employee.user_id.id for employee in gr_groups_config_ids.gr_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids=user_ids)
        self.state = 'confirm'

    @api.multi
    def set_to_draft(self):
        """
            sent the status of generating GR operation request in Set to Draft state
        """
        self.ensure_one()
        self.approved_by = False
        self.approved_date = False
        self.refused_by = False
        self.refused_date = False
        self.state = 'draft'

    @api.multi
    def inprogress_gr_operations(self):
        """
            sent the status of generating GR operation request is In progress state
        """
        self.ensure_one()
        self.write({'state': 'inprogress', 'approved_by': self.env.uid, 'approved_date': datetime.today()})

    @api.multi
    def refuse_gr_operations(self):
        """
            sent the status of generating GR operation request in Refuse state
        """
        self.ensure_one()
        return self.write({'state': 'refuse', 'refused_by': self.env.uid, 'refused_date': datetime.today()})

    @api.multi
    def received_gr_operations(self):
        """
            sent the status of generating GR operation request in Done state
        """
        self.ensure_one()
        self.state = 'done'

    @api.onchange('type_id')
    def onchange_type(self):
        """
            Set credit according to request type.
        """
        self.documents = self.type_id.documents
        self.expense_needed = self.type_id.expense_needed
        self.expense_total = 0
        self.company_contribution = 0
        self.emp_contribution = 0

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on selected employee
            job, department and company
        """
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id

    @api.multi
    def generate_expense(self):
        """
            Generate employee expense according to operation request
            return: created expense ID
        """
        self.ensure_one()
        product_id = self.env.ref('slnee_hr_gr_operation_request.operation_request')
        name = 'GR Operation - ' + self.name_get()[0][1]
        description = 'GR Operation - ' + self.name_get()[0][1]
        return self.generate_expense_payment(self, self.description, self.emp_contribution, self.company_contribution, self.payment_mode, name, product_id, self.expense_total)

    @api.multi
    def view_expense(self):
        """
            Redirect to open expense method.
        """
        for line in self:
            return self.redirect_to_expense(line.expense_ids)
