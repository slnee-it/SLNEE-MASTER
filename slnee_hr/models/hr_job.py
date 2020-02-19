# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'HR Job'

    arabic_name = fields.Char('Arabic Name')

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, department_id, company_id)', 'The name of the job position must be unique per department, grade and company!'),
    ]
