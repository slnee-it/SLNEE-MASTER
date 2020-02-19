# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _


class EmployeeReports(models.TransientModel):
    _name = "employee.head.count"

    based_on = fields.Selection([('Department', 'Department'), ('Job', 'Job'), ('Manager', 'Manager')], string='Based on')
    department_ids = fields.Many2many('hr.department', string='Department')
    job_ids = fields.Many2many('hr.job', string='Job')
    manager_ids = fields.Many2many('hr.employee', string='Manager')

    @api.multi
    def print_reports(self):
        self.ensure_one()
        return self.env.ref('slnee_hr.action_report_hr_employee').report_action(self)

    @api.onchange('based_on')
    def onchange_based_on(self):
        self.department_ids = False
        self.job_ids = False
        self.manager_ids = False

    @api.multi
    def get_dept(self):
        data = []
        if self.based_on == 'Department':
            if not self.department_ids:
                departments = self.env['hr.department'].search([])
            if self.department_ids:
                departments = self.env['hr.department'].search([('id', '=', self.department_ids.ids)])
            for department in departments:
                data.append(department.name)
        if self.based_on == 'Job':
            if not self.job_ids:
                jobs = self.env['hr.job'].search([])
            if self.job_ids:
                jobs = self.env['hr.job'].search([('id', '=', self.job_ids.ids)])
            for job in jobs:
                data.append(job.name)
        if self.based_on == 'Manager':
            if not self.manager_ids:
                managers = self.env['hr.employee'].search([('manager', '=', True)])
            if self.manager_ids:
                managers = self.env['hr.employee'].search([('id', '=', self.manager_ids.ids)])
            for manager in managers:
                data.append(manager.name)
        return data

    @api.multi
    def get_emp(self, data_id):
        emp = []
        if self.based_on == 'Department':
            dep = self.env['hr.department'].browse(data_id)
            employee = self.env['hr.employee'].search([('department_id', '=', dep.id)])
        if self.based_on == 'Job':
            job = self.env['hr.job'].browse(data_id)
            employee = self.env['hr.employee'].search([('job_id', '=', job.id)])
        if self.based_on == 'Manager':
            manager = self.env['hr.employee'].browse(data_id)
            employee = self.env['hr.employee'].search([('parent_id', '=', manager.id)])
        for rec in employee:
            emp_dict = {'code': rec.code,
                'name': rec.name,
                'joining_date': rec.date_of_join,
                'status': dict(rec._fields['employee_status'].selection).get(rec.employee_status)}
            emp.append(emp_dict)
        return emp
