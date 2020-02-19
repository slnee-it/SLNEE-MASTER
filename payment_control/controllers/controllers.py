# -*- coding: utf-8 -*-
from odoo import http

# class PaymentControl(http.Controller):
#     @http.route('/payment_control/payment_control/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payment_control/payment_control/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('payment_control.listing', {
#             'root': '/payment_control/payment_control',
#             'objects': http.request.env['payment_control.payment_control'].search([]),
#         })

#     @http.route('/payment_control/payment_control/objects/<model("payment_control.payment_control"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payment_control.object', {
#             'object': obj
#         })