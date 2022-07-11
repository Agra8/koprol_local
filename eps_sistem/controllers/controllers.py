# -*- coding: utf-8 -*-
# from odoo import http


# class EpsSistem(http.Controller):
#     @http.route('/eps_sistem/eps_sistem/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/eps_sistem/eps_sistem/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('eps_sistem.listing', {
#             'root': '/eps_sistem/eps_sistem',
#             'objects': http.request.env['eps_sistem.eps_sistem'].search([]),
#         })

#     @http.route('/eps_sistem/eps_sistem/objects/<model("eps_sistem.eps_sistem"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('eps_sistem.object', {
#             'object': obj
#         })
