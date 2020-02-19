# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCountry(models.Model):
    _inherit = 'res.country'

    arabic_country_name = fields.Char('Arabic Name', size=50)
