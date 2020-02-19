# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    po_box = fields.Char('PO Box')
    arabic_name = fields.Char('Arabic Name', size=120)
    arabic_city = fields.Char('Arabic City', size=120)
    arabic_street = fields.Char('Arabic Street', size=120)
    arabic_street2 = fields.Char('Arabic Street2', size=120)
