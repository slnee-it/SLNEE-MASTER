# -*- coding: utf-8 -*-
from odoo import http

# class PurchaseEncumberance(http.Controller):
#     @http.route('/purchase_encumberance/purchase_encumberance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_encumberance/purchase_encumberance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_encumberance.listing', {
#             'root': '/purchase_encumberance/purchase_encumberance',
#             'objects': http.request.env['purchase_encumberance.purchase_encumberance'].search([]),
#         })

#     @http.route('/purchase_encumberance/purchase_encumberance/objects/<model("purchase_encumberance.purchase_encumberance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_encumberance.object', {
#             'object': obj
#         })