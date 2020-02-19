# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    signature_image = fields.Binary(string='Signature', attachment=True)
