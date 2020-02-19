# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class HrDepartment(models.Model):
    _inherit = "hr.department"

    arabic_name = fields.Char('Arabic Name')
    manager_id = fields.Many2one('hr.employee', 'Head of Function')
