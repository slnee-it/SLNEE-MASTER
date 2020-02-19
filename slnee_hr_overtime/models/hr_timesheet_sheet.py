# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class HrContract(models.Model):
    _inherit = "hr.contract"
    _order = 'id desc'

    calculate_overtime = fields.Boolean('Calculate Overtime')
    overtime_limit = fields.Float(digits=(3, 2), string="Overtime Limit Hours")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
