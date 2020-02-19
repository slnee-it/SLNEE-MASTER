# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _


class CareerDevelopment(models.Model):
    _name = 'hr.career.development'
    _description = 'Employee Career Development Path'
    _rec_name = 'department_id'

    # Fields Hr Career Development

    department_id = fields.Many2one('hr.department', 'Department', required=True)
    career_line_ids = fields.One2many('hr.career.development.lines', 'career_id', 'Career Development functions')

    @api.multi
    @api.depends('department_id')
    def name_get(self):
        """
            Name get combination of Carrer Development Path of [`Department Name`]
        """
        result = []
        for record in self:
            name = ''.join(['Career Development Path of ', record.department_id.name or ''])
            result.append((record.id, name))
        return result


class CareerDevelopmentLines(models.Model):
    _name = 'hr.career.development.lines'

    # Fields Hr Career Development Lines

    career_id = fields.Many2one('hr.career.development', 'Career Development')
    global_functional_level = fields.Char('Global Functional Level', size=48)
    job_ids = fields.Many2many('hr.job', 'career_job_rel', 'career_line_id', 'job_id', 'Job Positions')
    avg_no_of_years = fields.Float('Average No. of Years')
    technical = fields.Char('Technical', size=256, required=True)
    milestones = fields.Text('Milestones', size=512, required=True)
    softskills = fields.Text('Soft Skills', size=256)
    other_non_mendatory = fields.Text('Other Non Mendatory', size=128)
