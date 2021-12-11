# -*- coding: utf-8 -*-
# from odoo import http


# class DmsHome(http.Controller):
#     @http.route('/dms_home/dms_home/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_home/dms_home/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_home.listing', {
#             'root': '/dms_home/dms_home',
#             'objects': http.request.env['dms_home.dms_home'].search([]),
#         })

#     @http.route('/dms_home/dms_home/objects/<model("dms_home.dms_home"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_home.object', {
#             'object': obj
#         })
