# -*- coding: utf-8 -*-
# from odoo import http


# class DmsBranch(http.Controller):
#     @http.route('/dms_branch/dms_branch/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_branch/dms_branch/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_branch.listing', {
#             'root': '/dms_branch/dms_branch',
#             'objects': http.request.env['dms_branch.dms_branch'].search([]),
#         })

#     @http.route('/dms_branch/dms_branch/objects/<model("dms_branch.dms_branch"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_branch.object', {
#             'object': obj
#         })
