# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _


class ResDocuments(models.Model):
    _inherit = 'res.documents'

    status = fields.Selection([('office', 'Office'), ('gr_user', 'GR User'),
                               ('employee', 'Employee')], string='Document Status')
