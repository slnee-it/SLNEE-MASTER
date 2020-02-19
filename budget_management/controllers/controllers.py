# -*- coding: utf-8 -*-
from odoo import http

# class BudgetManagement(http.Controller):
#     @http.route('/budget_management/budget_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/budget_management/budget_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('budget_management.listing', {
#             'root': '/budget_management/budget_management',
#             'objects': http.request.env['budget_management.budget_management'].search([]),
#         })

#     @http.route('/budget_management/budget_management/objects/<model("budget_management.budget_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('budget_management.object', {
#             'object': obj
#         })