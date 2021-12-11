# -*- coding: utf-8 -*-
# from odoo import http


# class DmsRequestForm(http.Controller):
#     @http.route('/dms_request_form/dms_request_form/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_request_form/dms_request_form/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_request_form.listing', {
#             'root': '/dms_request_form/dms_request_form',
#             'objects': http.request.env['dms_request_form.dms_request_form'].search([]),
#         })

#     @http.route('/dms_request_form/dms_request_form/objects/<model("dms_request_form.dms_request_form"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_request_form.object', {
#             'object': obj
#         })
