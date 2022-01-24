# -*- coding: utf-8 -*-
# from odoo import http


# class DmsDepartment(http.Controller):
#     @http.route('/dms_department/dms_department/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_department/dms_department/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_department.listing', {
#             'root': '/dms_department/dms_department',
#             'objects': http.request.env['dms_department.dms_department'].search([]),
#         })

#     @http.route('/dms_department/dms_department/objects/<model("dms_department.dms_department"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_department.object', {
#             'object': obj
#         })
