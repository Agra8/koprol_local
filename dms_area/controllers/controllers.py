# -*- coding: utf-8 -*-
# from odoo import http


# class DmsArea(http.Controller):
#     @http.route('/dms_area/dms_area/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_area/dms_area/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_area.listing', {
#             'root': '/dms_area/dms_area',
#             'objects': http.request.env['dms_area.dms_area'].search([]),
#         })

#     @http.route('/dms_area/dms_area/objects/<model("dms_area.dms_area"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_area.object', {
#             'object': obj
#         })
