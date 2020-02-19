# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Employee(models.Model):
    _inherit = "hr.employee"

    issue_warning_ids = fields.Many2many('issue.warning', string='Warnings')
    warning_count = fields.Integer(compute='_compute_warning_count', string='Warnings')

    def _compute_warning_count(self):
        for employee in self:
            warning_ids = self.env['issue.warning'].search(['|', ('employee_id', '=', employee.id), ('employee_ids', '=', employee.id)])
            employee.warning_count = len(warning_ids) if warning_ids else 0

    @api.multi
    def act_hr_employee_warning(self):
        action = self.env.ref('hr_warning.act_issue_warning').read()[0]
        warning_ids = self.env['issue.warning'].search(['|', ('employee_id', '=', self.id), ('employee_ids', '=', self.id)])
        if len(warning_ids) > 1:
            action['domain'] = [('id', 'in', warning_ids.ids)]
        elif len(warning_ids) == 1:
            action['views'] = [(self.env.ref('hr_warning.hr_warning_view_form').id, 'form')]
            action['res_id'] = warning_ids[0].id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
