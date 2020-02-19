# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from datetime import datetime, timedelta
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class leaves_allocation(models.TransientModel):
    _name = 'leaves.allocation'
    _description = "Leaves Allocation"

    @api.model
    def get_leave_type(self):
        """
            Returns the leave types with its ID
        """
        leave_types = {
            'annual_leave': self.env.ref('hr_holidays.holiday_status_cl'),
            'sick_leave': self.env.ref('hr_holidays.holiday_status_sl'),
            'study_leave': self.env.ref('hr_holidays.holiday_status_comp'),
            'maternity_leave': self.env.ref('slnee_hr_leaves_management.holiday_status_maternity'),
            'marrige_leave': self.env.ref('slnee_hr_leaves_management.holiday_status_marriage'),
            'compassionate_leave': self.env.ref('slnee_hr_leaves_management.holiday_status_compassionate'),
            'paternity_leave': self.env.ref('slnee_hr_leaves_management.holiday_status_paternity'),
            'hajj_leave': self.env.ref('slnee_hr_leaves_management.holiday_status_hajj'),
            'secondment_leave': self.env.ref('slnee_hr_leaves_management.holiday_status_secondment'),
        }
        return leave_types

    @api.model
    def _get_default_year(self):
        """
            Get the default year
        """
        res = self.env['year.year'].find(time.strftime("%Y-%m-%d"), True, False)
        return res if res else False

    is_auto_validate = fields.Boolean(string="Auto Validate")
    is_double_validation = fields.Boolean(string="Auto Double Validate")
    double_validation = fields.Boolean(related="holiday_status_id.double_validation", string="Double Validation")
    name = fields.Char('Task Name', size=256, required=True)
    holiday_status_id = fields.Many2one("hr.holidays.status", "Leave Type", required=True)
    number_of_days_temp = fields.Float('Allocation', required=True)
    fiscalyear = fields.Many2one('year.year', 'Fiscal Year', required=True, default=_get_default_year)
    date = fields.Date('Date', required=True, default=fields.Date.today())
    company_id = fields.Many2one('res.company', 'Company', required=True,
                            default=lambda self: self.env['res.company']._company_default_get('leaves.allocation'))
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    carry_forward = fields.Boolean("Carry Forward")
    carry_forward_limit = fields.Float('Carry Forward', digits=(3, 2))
    override = fields.Boolean("Override", default=False)
    override_limit = fields.Float('Override Limit', digits=(3, 2))
    employee_ids = fields.One2many('leaves.allocation.employee', 'leaves_allocation_id', string='Employees')
    target = fields.Selection([('all', 'All Employee'), ('branch', 'Office Wise'), ('department', 'Department Wise'), ('job', 'Job Profile Wise')], string="Target Group", default='department')
    branch_ids = fields.Many2many('hr.branch', 'branch_leaves_allocation_rel', 'leaves_allocation_id', 'branch_id', string="Office")
    department_ids = fields.Many2many('hr.department', 'department_leaves_allocation_rel', 'leaves_allocation_id', 'department_id', string="Departments")
    job_ids = fields.Many2many('hr.job', 'job_leaves_allocation_rel', 'leaves_allocation_id', 'job_id', string="JOB Profiles")

    @api.onchange('target', 'branch_ids', 'department_ids', 'job_ids')
    def onchange_target(self):
        """
            onchange the target, branches, departments and jobs
        """
        emp_obj = self.env['hr.employee']
        employee = []
        leave_types = self.get_leave_type()
        holiday_status = self.holiday_status_id and self.holiday_status_id.name or ''

        def get_details(employee_id):
            res = {'department_id': False}
            if employee_id:
                return {'employee_id': employee_id.id,
                        'department_id': employee_id.department_id and employee_id.department_id.id or False,
                        }
            return res

        domain = [('active', '=', True), ('date_of_leave', '=', False)]
        if self.target == 'branch':
            branch_ids = [branch.id for branch in self.branch_ids if self.branch_ids]
            domain.append(('branch_id', 'in', branch_ids))
        elif self.target == 'department':
            department_ids = [department.id for department in self.department_ids if self.department_ids]
            domain.append(('department_id', 'in', department_ids))
        elif self.target == 'job':
            job_ids = [job.id for job in self.job_ids if self.job_ids]
            domain.append(('job_id', 'in', job_ids))

        if holiday_status == leave_types['maternity_leave'].name:
            domain.append(('marital', '!=', 'single'))
            domain.append(('gender', '=', 'female'))

        elif holiday_status == leave_types['paternity_leave'].name:
            domain.append(('marital', '=', 'married'))
            domain.append(('gender', '=', 'male'))

        elif holiday_status == leave_types['marrige_leave'].name:
            domain.append(('marital', '=', 'single'))

        elif holiday_status == leave_types['hajj_leave'].name:
            # After 2 Year of date of join.
            duration = datetime.now() - timedelta(days=2 * 365)
            domain.append(('religion', '=', 'muslim'))
            domain.append(('date_of_join', '<', duration.strftime("%Y-%m-%d")))

        elif holiday_status == leave_types['annual_leave'].name:
            # After 3 Month of date of join.
            duration = datetime.now() - timedelta(3 * 365 / 12)
            domain.append(('date_of_join', '<', duration.strftime("%Y-%m-%d")))

        if self.target:
            for emp_id in emp_obj.search(domain):
                res = get_details(emp_id)
                employee.append(res)
        self.employee_ids = employee

    @api.onchange('holiday_status_id')
    def onchange_holiday_status(self):
        """
            allocate default values of no of days based on select holiday status
        """
        self.carry_forward = False
        self.override = False
        if self.holiday_status_id:
            leave_types = self.get_leave_type()
            if self.holiday_status_id.carry_forward:
                self.carry_forward = True
            if self.holiday_status_id.limit:
                self.override = False

            number_of_days_temp = 0.0
            if self.holiday_status_id.name == leave_types['maternity_leave'].name:
                number_of_days_temp = 50.00
            elif self.holiday_status_id.name == leave_types['paternity_leave'].name:
                number_of_days_temp = 3.00
            elif self.holiday_status_id.name == leave_types['compassionate_leave'].name:
                number_of_days_temp = 5.00
            elif self.holiday_status_id.name == leave_types['marrige_leave'].name:
                number_of_days_temp = 3.00
            elif self.holiday_status_id.name == leave_types['hajj_leave'].name:
                number_of_days_temp = 5.00
            elif self.holiday_status_id.name == leave_types['annual_leave'].name:
                number_of_days_temp = 25.00
                self.carry_forward_limit = 5
            elif self.holiday_status_id.name == leave_types['sick_leave'].name:
                number_of_days_temp = 90.00
            elif self.holiday_status_id.name == leave_types['study_leave'].name:
                number_of_days_temp = 10.00
            elif self.holiday_status_id.name == leave_types['secondment_leave'].name:
                number_of_days_temp = 365.00
            self.number_of_days_temp = number_of_days_temp

    @api.multi
    def allocate_leave(self):
        """
            allocate leave with complete workflow
        """
        self.ensure_one()
        if not self.employee_ids:
            raise UserError(_('Please select employee!'))
        hr_holidays_obj = self.env['hr.holidays']
        res = {
            'name': self.name,
            'holiday_status_id': self.holiday_status_id.id,
            'number_of_days_temp': self.number_of_days_temp,
            'fiscalyear': self.fiscalyear and self.fiscalyear.id,
            'company_id': self.company_id and self.company_id.id,
            'notes': self.description,
            'user_id': self.user_id and self.user_id.id,
            'carry_forward': self.carry_forward,
            'carry_forward_limit': self.carry_forward_limit,
            'limit': self.override,
            'override_limit': self.override_limit,
            'type': 'add',
        }
        if self.employee_ids:
            leave_types = self.get_leave_type()
            holiday_list = []
            for employee_obj in self.employee_ids:
                if self.holiday_status_id.one_time_usable:
                    leave_request_ids = hr_holidays_obj.search([('employee_id', '=', employee_obj.employee_id and employee_obj.employee_id.id),
                            ('holiday_status_id', '=', self.holiday_status_id and self.holiday_status_id.id),
                            ('type', '=', 'remove'), ('state', '=', 'validate')])
                    if leave_request_ids:
                        continue
                status = self.holiday_status_id
                res.update({'employee_id': employee_obj.employee_id and employee_obj.employee_id.id})
                holidays_allocation = hr_holidays_obj.create(res)
                holiday_list.append(holidays_allocation.id)
                holidays_allocation.onchange_carryforward()
                res.update({'message_follower_ids':[]})
                if self.is_auto_validate:
                    holidays_allocation.action_approve()
                if self.is_double_validation:
                    holidays_allocation.action_validate()
        if holiday_list:
            action = self.env.ref('hr_holidays.open_department_holidays_allocation_approve').read()[0]
            action['context'] = {}
            if len(holiday_list) > 1:
                action['domain'] = [('id', 'in', holiday_list)]
            elif len(holiday_list) == 1:
                action['views'] = [(self.env.ref('hr_holidays.edit_holiday_new').id, 'form')]
                action['res_id'] = holiday_list[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action


class leaves_allocation_employee(models.TransientModel):
    _name = "leaves.allocation.employee"
    _description = "Leaves Allocation Employee"

    leaves_allocation_id = fields.Many2one('leaves.allocation', 'Leaves Allocation')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    department_id = fields.Many2one('hr.department', 'Department')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
            set the details of code and department based on select employee
        """
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id and self.employee_id.department_id.id or False
