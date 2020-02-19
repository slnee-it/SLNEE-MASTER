# -*- coding: utf-8 -*-
from odoo import http

# class BillsEncumberance(http.Controller):
#     @http.route('/bills_encumberance/bills_encumberance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bills_encumberance/bills_encumberance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bills_encumberance.listing', {
#             'root': '/bills_encumberance/bills_encumberance',
#             'objects': http.request.env['bills_encumberance.bills_encumberance'].search([]),
#         })

#     @http.route('/bills_encumberance/bills_encumberance/objects/<model("bills_encumberance.bills_encumberance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bills_encumberance.object', {
#             'object': obj
#         })