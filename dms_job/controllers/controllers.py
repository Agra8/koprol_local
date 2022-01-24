# -*- coding: utf-8 -*-
# from odoo import http


# class DmsJob(http.Controller):
#     @http.route('/dms_job/dms_job/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_job/dms_job/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_job.listing', {
#             'root': '/dms_job/dms_job',
#             'objects': http.request.env['dms_job.dms_job'].search([]),
#         })

#     @http.route('/dms_job/dms_job/objects/<model("dms_job.dms_job"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_job.object', {
#             'object': obj
#         })
