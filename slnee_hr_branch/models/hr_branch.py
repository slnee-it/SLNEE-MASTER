# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class HrBranch(models.Model):
    _name = 'hr.branch'

    def _default_branch(self):
        """
            Default Get branch from current user.
        """
        pass
        # branch_ids = self.env['hr.branch'].search(
        #     [('company_id', '=', self.env.user.company_id.id)])
        # return branch_ids and branch_ids[0] or False

    name = fields.Char('Office Name', size=64, required=True)
    arabic_name = fields.Char('Arabic Name', size=64)
    code = fields.Char('Code', size=64, required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    company_name = fields.Char('Company Name', size=128)
    company_arabic_name = fields.Char('Company Arabic Name', size=128)
    street = fields.Char('Street', size=128)
    street2 = fields.Char('Street2', size=128)
    zip = fields.Char('Zip', change_default=True, size=24)
    city = fields.Char('City', size=128)
    po_box_no = fields.Char('P.O.Box', size=128)
    country = fields.Char('Country', size=128)
    arabic_street = fields.Char('Street', size=128)
    arabic_street2 = fields.Char('Street2', size=128)
    arabic_city = fields.Char('City', size=128)
    arabic_country = fields.Char('Country', size=128)
    phone = fields.Char('Tel', size=18)
    mobile = fields.Char('Mobile', size=18)
