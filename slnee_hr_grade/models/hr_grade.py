# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _


class HrGrade(models.Model):
    _name = 'hr.grade'
    _description = "Grade Description"

    name = fields.Char('Name', required=True)
    hr_job_ids = fields.One2many('hr.job', 'grade_id', 'Job')
    is_above_manager = fields.Boolean('Is Above Manager', help="Tick this if grade is above manager level.")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    grade_id = fields.Many2one('hr.grade', 'Grade')

    @api.onchange('grade_id')
    def onchange_grade_id(self):
        """
            If Change the Grade, Job also changed.
        """
        self.job_id = False
        return {'domain': {'job_id': [('id', 'in', self.grade_id.hr_job_ids.ids)]}}


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'HR Job'

    grade_id = fields.Many2one('hr.grade', string='Grade')

    @api.multi
    @api.depends('name', 'grade_id')
    def name_get(self):
        """
            getting the name with combination of name and grade name
            for eg. Name: John, Grade: First output: `John(First)`
        """
        res = []
        for record in self:
            name = record.name or ''
            if record.grade_id:
                name = ''.join([record.name, '(', record.grade_id.name, ')'])
            res.append((record.id, name))
        return res
