# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _

class EmployeeBonus(models.Model):
    _inherit = 'employee.bonus'

    grade_id = fields.Many2one('hr.grade', string='Grade', readonly=True)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
           onchange the value based on selected employee,
           grade
        """
        super(EmployeeBonus, self).onchange_employee_id()
        self.grade_id = False
        if self.employee_id:
            self.grade_id = self.employee_id.grade_id.id

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'grade_id':employee.grade_id.id,
            })
        return super(EmployeeBonus, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'grade_id':employee.grade_id.id,
            })
        return super(EmployeeBonus, self).write(values)

class EmployeeBonusLines(models.Model):
    _inherit = 'employee.bonus.lines'

    grade_id = fields.Many2one('hr.grade', string='Grade', readonly=False)
    new_grade_id = fields.Many2one('hr.grade', string='To Grade')

    @api.onchange('new_grade_id')
    def onchange_new_grade(self):
        """
           onchange the value based on selected new grade,
           new job
        """
        self.new_job_id = False
        res = {}
        if self.new_grade_id:
            job_ids = self.env['hr.job'].sudo().search([('grade_id', '=', self.new_grade_id.id)])
            if job_ids:
                return {'domain': {'new_job_id': [('id', 'in', job_ids.ids)]}}
        else:
            return {'domain': {'new_job_id': [('id', 'in', [])]}}
