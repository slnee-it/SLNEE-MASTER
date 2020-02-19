# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrPayslipExport(models.Model):
    _name = 'hr.payslip.export'
    _description = "Payslip Export"

    name = fields.Char('Name', required=True)
    line_ids = fields.One2many('hr.payslip.export.line','payslip_export_id','Export line')


class HrPayslipExportLine(models.Model):
    _name = 'hr.payslip.export.line'
    _order = 'sequence'
    _description = "Payslip Export Line"

    sequence = fields.Integer('Sequence', default=5)
    rule_id = fields.Many2one('hr.salary.rule','Rule',required=False)
    payslip_export_id = fields.Many2one('hr.payslip.export','Payslip Export')
    is_difference_field = fields.Boolean('Is Difference Field')
