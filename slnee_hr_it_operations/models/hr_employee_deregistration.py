# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import time


class HRDeregistration(models.Model):

    _name = 'hr.employee.deregistration'
    _inherit = 'mail.thread'
    _description = "Employee De-Registration"
    _rec_name = 'employee_name'

    @api.multi
    def unlink(self):
        '''
            Delete / remove a record
        '''
        for objects in self:
            if objects.state in ['confirm', 'receive', 'validate', 'approve', 'done', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HRDeregistration, self).unlink()

    # Fields HR DE-Registration
    handled_by = fields.Many2one('hr.employee', 'Handled by')
    register_employee_id = fields.Many2one('hr.employee.registration', 'Register Employee', required=True)
    employee_name = fields.Char(string='Name', related='register_employee_id.employee_name')
    deregistration_date = fields.Date('De-Registration Date', default=time.strftime('%Y-%m-%d'))
    last_working_day = fields.Date('Last Working Day')
    laptop_desktop = fields.Char("Laptop/Desktop")
    laptop_desktop_serial = fields.Char('Serial No.')
    token_serial = fields.Char('Token Serial No.')
    access_card = fields.Char('Access Card')
    is_charger = fields.Boolean("Charger")
    is_carrying_case = fields.Boolean("Carrying case")
    is_other = fields.Boolean("Other")
    is_format_data = fields.Boolean("Client Data Removed from Hard Drive")
    is_iid = fields.Boolean("Deletion of IID")
    is_exchange_mbox = fields.Boolean("Exchange M.box")
    is_personal_folder = fields.Boolean("Personal Folder")
    is_nt_account = fields.Boolean("NT Account")
    is_remote_access = fields.Boolean("Remote Access")
    is_token_retrieved = fields.Boolean("Token Retrieved")
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
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
           ('done', 'Done')], 'Status', default='draft')  # ,track_visibility='onchange'),

    @api.onchange('register_employee_id')
    def onchange_register_employee_id(self):
        '''
            set details of employee like Laptop, Desktop, Token Series, etc.
            Based on select or Register Employee.
        '''
        self.department_id = self.register_employee_id.department_id.id or False
        self.laptop_desktop = self.register_employee_id.laptop_desktop or ''
        self.laptop_desktop_serial = self.register_employee_id.laptop_desktop_serial or ''
        self.token_serial = self.register_employee_id.token_serial or ''
        self.access_card = self.register_employee_id.access_card or ''
        self.is_charger = self.register_employee_id.is_charger
        self.is_carrying_case = self.register_employee_id.is_carrying_case
        self.is_other = self.register_employee_id.is_other

    @api.multi
    def write(self, vals):
        '''
            update an existing record
        '''
        if vals.get('register_employee_id', False):
            employee = self.env['hr.employee.registration'].browse(vals['register_employee_id'])
            vals.update({'department_id': employee.department_id.id or False, })
        return super(HRDeregistration, self).write(vals)

    @api.model
    def create(self, vals):
        '''
            Create a new record
        '''
        if vals.get('register_employee_id', False):
            employee = self.env['hr.employee.registration'].browse(vals['register_employee_id'])
            vals.update({'department_id': employee.department_id.id or False, })
        return super(HRDeregistration, self).create(vals)

    @api.multi
    def deregister_confirm(self):
        '''
            set Deregistration of employee confirmed.
        '''
        self.ensure_one()
        self.state = 'confirm'

    @api.multi
    def deregister_receive(self):
        '''
            Employee Received Deregistration.
        '''
        self.ensure_one()
        self.state = 'receive'

    @api.multi
    def deregister_validate(self):
        '''
            Employee Deregistration validate.
        '''
        self.ensure_one()
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'validate', 'validated_by': user.id, 'validated_date': today})

    @api.multi
    def deregister_approve(self):
        '''
            Employee Deregistration Approve.
        '''
        self.ensure_one()
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'approve', 'approved_by': user.id, 'approved_date': today})

    @api.multi
    def deregister_cancel(self):
        '''
            Employee Deregistration cancel / refuse.
        '''
        self.ensure_one()
        self.state = 'refuse'

    @api.multi
    def deregister_done(self):
        '''
            Employee Deregistration done.
        '''
        self.ensure_one()
        self.register_employee_id.state = 'refuse'
        self.state = 'done'

    @api.multi
    def set_to_draft(self):
        '''
            Employee Deregistration Reset to Draft or initial state.
        '''
        self.ensure_one()
        self.state = 'draft'
