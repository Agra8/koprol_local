# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class website_request_form(models.Model):
#     _name = 'website_request_form.website_request_form'
#     _description = 'website_request_form.website_request_form'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
