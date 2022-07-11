# -*- coding: utf-8 -*-
# from odoo import http


# class DmsTeams(http.Controller):
#     @http.route('/dms_teams/dms_teams/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dms_teams/dms_teams/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dms_teams.listing', {
#             'root': '/dms_teams/dms_teams',
#             'objects': http.request.env['dms_teams.dms_teams'].search([]),
#         })

#     @http.route('/dms_teams/dms_teams/objects/<model("dms_teams.dms_teams"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dms_teams.object', {
#             'object': obj
#         })
