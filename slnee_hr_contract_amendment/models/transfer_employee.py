# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
import time
from odoo import SUPERUSER_ID

# html_data = """
#     <html>
#     <head>
#     <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
#     </head>
#     <body>
#     <table border="0" cellspacing="10" cellpadding="0" width="100%%"
#     style="font-family: Arial, Sans-serif; font-size: 14">
#     <tr>
#         <td width="100%%">Hello
#         AMENDMENT TO CONTRACT Employment Agreement
#         Between your company
#         and %s dated %s
#         <br/>
#         The following amendments/add to above referenced contract will be made effective from %s
#         Paragraph %s in the above reference contract your compnay and %s
#         acknowledge that as of %s the employee will transfer from %s %s to %s %s
#         the employees %s, %s and %s will be replaced with %s - %s %s,%s
#         Paragraph Other your current base location %s will change to %s.
#     </td>
#     </tr>
#     </table>
#     </body>
#     </html>"""


class TransferEmployee(models.Model):

    _name = 'transfer.employee'
    _inherit = 'mail.thread'
    _description = "Transfer Employee"
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    hr_contract_id = fields.Many2one('hr.contract', 'Contract', required=True, domain=[('employee_id', '=', 'employee_id.id')])
    grade_id = fields.Many2one('hr.grade', 'From Grade', readonly=True)
    job_id = fields.Many2one('hr.job', 'From Job', readonly=True)
    department_id = fields.Many2one('hr.department', 'From Department', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('hr.branch', 'From Office', readonly=True)
    effective_date = fields.Date('Effective Date', default=time.strftime('%Y-%m-%d'))
    new_department_id = fields.Many2one('hr.department', 'To Department')
    new_grade_id = fields.Many2one('hr.grade', 'To Grade')
    new_job_id = fields.Many2one('hr.job', 'To Job')
    new_branch_id = fields.Many2one('hr.branch', 'To Office')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'), ('approve', 'Approved'), ('done', 'Done'), ('cancel', 'Cancel')], 'State', default='draft', track_visibility='onchange')
    description = fields.Text('Description')
    approved_date = fields.Datetime('Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    validated_by = fields.Many2one('res.users', 'Validated by', readonly=True, copy=False)
    validated_date = fields.Datetime('Validated Date', readonly=True, copy=False)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        effective_date = time.strftime('%Y-%m-%d')
        payslip_obj = self.env['hr.payslip']
        contract_ids = payslip_obj.get_contract(self.employee_id, effective_date, effective_date)
        contract = payslip_obj.browse(contract_ids)
        self.department_id = self.employee_id.department_id.id or False
        self.branch_id = self.employee_id.branch_id.id or False
        self.job_id = self.employee_id.job_id.id or False
        self.grade_id = self.employee_id.grade_id.id or False
        self.hr_contract_id = contract and contract[0].id or False

    @api.model
    def create(self, vals):
        if vals.get('employee_id', False):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id or False,
                         'branch_id': employee.branch_id.id or False,
                         'job_id': employee.job_id.id or False,
                         'grade_id': employee.grade_id.id or False,
            })
        return super(TransferEmployee, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('employee_id', False):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            vals.update({'department_id': employee.department_id.id or False,
                        'branch_id': employee.branch_id.id or False,
                        'job_id': employee.job_id.id or False,
                        'grade_id': employee.grade_id.id or False,
            })
        return super(TransferEmployee, self).write(vals)

    @api.multi
    @api.depends('employee_id')
    def name_get(self):
        result = []
        for transfer in self:
            name = transfer.employee_id.name or ''
            result.append((transfer.id, name))
        return result

    @api.multi
    def unlink(self):
        for objects in self:
            if objects.state in ['confirm', 'validate', 'approve', 'done', 'cancel']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(TransferEmployee, self).unlink()

    @api.multi
    def transfer_confirm(self):
        self.ensure_one()
        warnings = self.env['issue.warning'].search([('id', 'in', self.employee_id.issue_warning_ids.ids), ('warning_action', '=', 'prohibit'), ('state', '=', 'done')])
        for warning in warnings:
            if self.effective_date >= warning.start_date and self.effective_date <= warning.end_date:
                raise UserError(_("You can't Confirm Contract Amendment because %s have Prohibit Benefit Upgrades Warning.") % self.employee_id.name)
        self.write({'state': 'confirm'})

    @api.multi
    def transfer_validate(self):
        self.ensure_one()
        hop_groups_config_obj = self.env['hr.groups.configuration']
        hop_groups_config_ids = hop_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id or False), ('hop_ids', '!=', False)])
        user_ids = hop_groups_config_ids and [employee.user_id.id for employee in hop_groups_config_ids.hop_ids if employee.user_id] or []
        self.message_subscribe_users(user_ids)
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'validate', 'validated_by': user.id, 'validated_date': today})

    @api.multi
    def transfer_approve(self):
        self.ensure_one()
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'approve', 'approved_by': user.id, 'approved_date': today})

    @api.multi
    def transfer_done(self):
        self.ensure_one()
        # value = self.env['hr.employee'].browse(self.employee_id.id)
        self.employee_id.department_id = self.new_department_id.id or False
        self.employee_id.branch_id = self.new_branch_id.id or False
        self.employee_id.grade_id = self.new_grade_id.id or False
        self.employee_id.job_id = self.new_job_id.id or False
        # job_rec_obj = self.env['hr.job.requisition'].search([('state','=','launch'),('job_id','=',self.new_job_id.id ),('department_id','=',self.new_department_id.id)])
        # if job_rec_obj:
        #     if job_rec_obj.expected_employees == job_rec_obj.no_of_employee:
        #         job_rec_obj.state = 'done'
        self.write({'state': 'done'})

    @api.multi
    def transfer_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})

    @api.multi
    def set_to_draft(self):
        self.ensure_one()
        # value = self.env['hr.employee'].browse(self.employee_id.id)
        self.employee_id.department_id = self.department_id.id or False
        self.employee_id.branch_id = self.branch_id.id or False
        self.employee_id.grade_id = self.grade_id.id or False
        self.employee_id.job_id = self .job_id.id or False
        self.write({'state': 'draft'})
