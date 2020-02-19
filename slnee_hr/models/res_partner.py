# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    institute = fields.Boolean('Institute', help="Check this box if this contact is a institute.")
    employee = fields.Boolean('Employee')
    arabic_name = fields.Char('Arabic Name', size=120)
