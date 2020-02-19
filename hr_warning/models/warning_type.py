# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class WarningType(models.Model):
    _name = "warning.type"

    name = fields.Char(string='Name', required = True)
    description = fields.Html(string='Description')
    warning_action = fields.Selection([('expiry', 'Expiry Period'), ('deduct', 'Deduct from Salary or not'), ('prohibit', 'Prohibit Benefit Upgrades')], string="Warning Action")
    color = fields.Integer(string='Color')