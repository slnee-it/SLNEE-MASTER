# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
import time


class EquipmentRegistration(models.Model):
    _name = 'equipment.registration'
    _description = "Equipment Registration"

    reg_id = fields.Many2one('hr.employee.registration', 'IT Department')
    item = fields.Char('Item', required="True")
    item_state = fields.Selection([('yes', 'YES'), ('no', 'NO'), ('na', 'N/A')], 'Status', required="True")
    category_id = fields.Many2one('maintenance.equipment.category', string='Equipment Category', required="True")
    handled_by = fields.Many2one('hr.employee', 'Handled by')
    remarks = fields.Char('Remarks')


class HRRegistration(models.Model):
    _name = 'hr.employee.registration'
    _inherit = 'mail.thread'
    _description = "Employee Registration"
    _rec_name = 'employee_name'

    @api.model
    def get_employee(self):
        """
            Get Employee record depends on current user.
        """
        employee_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return employee_ids[0] if employee_ids else False

    @api.model
    def _get_equipment_registration(self):
        equipment_registration_lines = []
        equipment_registration_ids = self.env['equipment.registration'].search([('reg_id', '=', self.id)])
        for clearance_dept_id in equipment_registration_ids:
            equipment_registration_lines.append((0, 0, {'item': clearance_dept_id.item,
                              'item_state': clearance_dept_id.item_state,
                              'category_id': clearance_dept_id.category_id.id,
                              }))  # this dict contain keys which are fields of one2many field
        return equipment_registration_lines

    @api.multi
    def unlink(self):
        '''
            Remove record
        '''
        for objects in self:
            if objects.state in ['confirm', 'receive', 'validate', 'approve', 'done', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HRRegistration, self).unlink()

    # Fields HR Registration
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, domain="[('active', '=', True)]", default=get_employee)
    employee_name = fields.Char(string='Name', related='employee_id.name')
    handled_by = fields.Many2one('hr.employee', 'Handled by')
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    registration_date = fields.Date('Registration Date', default=time.strftime('%Y-%m-%d'))
    email = fields.Char("Email")
    approved_date = fields.Datetime('Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    validated_by = fields.Many2one('res.users', 'Validated by', readonly=True, copy=False)
    validated_date = fields.Datetime('Validated Date', readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'),
           ('confirm', 'Waiting Approval'),
           ('receive', 'Received'),
           ('validate', 'Validated'),
           ('approve', 'Approved'),
           ('refuse', 'Refused'),
           ('done', 'Done')], 'Status', default='draft', track_visibility='onchange')
    it_dept_ids = fields.One2many('equipment.registration', 'reg_id', 'IT Departments', ondelete='cascade', default=_get_equipment_registration)

    _sql_constraints = [
        ('employee_unique', 'unique(employee_id)', 'This employee registration process is already done.'),
    ]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        '''
            Department Details set based on Employee selection.
        '''
        self.department_id = self.employee_id.department_id.id or False

    def _make_equipment_request(self, values):
        equipment_request_obj = self.env['maintenance.equipment.request']
        employee = values.get('employee_id', self.employee_id.id)
        for value in values.get('it_dept_ids'):
            if value[2] and value[2].get('item_state') == 'yes':
                equipment = {'category_id': value[2].get('category_id',),
                             'assign_to': 'employee', 'employee_id': employee,
                             'name': value[2].get('item')}
                equipment_request_obj.create(equipment)

    @api.model
    def create(self, vals):
        '''
            Create a new record
        '''
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id or False})
        if vals.get('it_dept_ids'):
            self._make_equipment_request(vals)
        return super(HRRegistration, self).create(vals)

    @api.multi
    def write(self, vals):
        '''
            Update an existing record
        '''
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id or False})
        return super(HRRegistration, self).write(vals)

    @api.multi
    def register_confirm(self):
        '''
            set Registration of employee confirmed.
        '''
        self.ensure_one()
        self.state = 'confirm'

    @api.multi
    def register_receive(self):
        '''
            Employee Received Registration.
        '''
        self.ensure_one()
        self.state = 'receive'

    @api.multi
    def register_validate(self):
        '''
            Employee Registration validate.
        '''
        self.write({'state': 'validate', 'validated_by': self.env.uid, 'validated_date': fields.Datetime.now()})

    @api.multi
    def register_approve(self):
        '''
            Employee Registration Approve.
        '''
        self.ensure_one()
        self.write({'state': 'approve', 'approved_by': self.env.uid, 'approved_date': fields.Datetime.now()})

    @api.multi
    def register_cancel(self):
        '''
            Employee Registration cancel / refuse.
        '''
        self.ensure_one()
        self.state = 'refuse'

    @api.multi
    def register_done(self):
        '''
            Employee Registration done.
        '''
        self.ensure_one()
        self.state = 'done'

    @api.multi
    def set_to_draft(self):
        '''
            Employee Registration Reset to Draft or initial state.
        '''
        self.ensure_one()
        self.state = 'draft'
