# -*- coding: utf-8 -*-
# from odoo import http


# class DmsEmployee(http.Controller):
#     @http.route('/dms_employee/dms_employee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_employee/dms_employee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_employee.listing', {
#             'root': '/dms_employee/dms_employee',
#             'objects': http.request.env['dms_employee.dms_employee'].search([]),
#         })

#     @http.route('/dms_employee/dms_employee/objects/<model("dms_employee.dms_employee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_employee.object', {
#             'object': obj
#         })
