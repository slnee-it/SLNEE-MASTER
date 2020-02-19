# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class HrGroupsConfiguration(models.Model):
    _name = "hr.groups.configuration"
    _rec_name = 'branch_id'
    _description = "HR Groups Configuration"

    # Fields Hr Groups Configuration

    branch_id = fields.Many2one('hr.branch', 'Office', required=True)
    helpdesk_ids = fields.Many2many('hr.employee', 'employee_helpdesk_rel', 'helpdesk_id', 'employee_id', string='Helpdesks')
    talent_acquisition_ids = fields.Many2many('hr.employee', 'employee_talent_rel', 'talent_acqui_id', 'employee_id', string='Talent Acquisitions')
    gr_ids = fields.Many2many('hr.employee', 'employee_gr_rel', 'gr_id', 'employee_id', string='GRs')
    hr_ids = fields.Many2many('hr.employee', 'employee_hr_rel', 'hr_id', 'employee_id', string='HRs')
    finance_ids = fields.Many2many('hr.employee', 'employee_finance_rel', 'finance_id', 'employee_id', string='Finances')
    admin_ids = fields.Many2many('hr.employee', 'employee_admin_rel', 'admin_id', 'employee_id', string='Admins')
    payroll_ids = fields.Many2many('hr.employee', 'employee_payroll_rel', 'payroll_id', 'employee_id', string='Payrolls')
    driver_ids = fields.Many2many('hr.employee', 'employee_driver_rel', 'driver_id', 'employee_id', string='Drivers')
    hop_ids = fields.Many2many('hr.employee', 'employee_hop_rel', 'hop_id', 'employee_id', string='HoPs')

    _sql_constraints = [
        ('unique_branch_id', 'unique(branch_id)', 'Office must be unique per Configuration!'),
    ]

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        """
            when we change the branch, effects on help desk, talent acquisition, GR, HR, etc.
        """
        self.helpdesk_ids = False
        self.talent_acquisition_ids = False
        self.gr_ids = False
        self.hr_ids = False
        self.finance_ids = False
        self.admin_ids = False
        self.payroll_ids = False
        self.driver_ids = False
        self.hop_ids = False
