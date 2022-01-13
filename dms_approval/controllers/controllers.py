# -*- coding: utf-8 -*-
# from odoo import http


# class DmsApproval(http.Controller):
#     @http.route('/dms_approval/dms_approval/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_approval/dms_approval/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_approval.listing', {
#             'root': '/dms_approval/dms_approval',
#             'objects': http.request.env['dms_approval.dms_approval'].search([]),
#         })

#     @http.route('/dms_approval/dms_approval/objects/<model("dms_approval.dms_approval"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_approval.object', {
#             'object': obj
#         })
