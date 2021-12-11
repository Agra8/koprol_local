#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ResBranch(models.Model):

    _name= "res.branch"
    _description = "Res Branch"

    # 7: defaults methods

    def get_default_date(self):
        return (datetime.now() + relativedelta(hours=7)).date()

    def _get_default_datetime_plus_7(self):
        return datetime.now() + timedelta(hours=7)
    
    def get_default_datetime(self):
        return datetime.now()
    
    # 8: fields
    name = fields.Char(required=True, string='Name',  help='')
    code = fields.Char(string='Dealer Code', help='')
    is_md = fields.Boolean('Is Main Dealer')
    active = fields.Boolean(string="Active", default = True,  help="")
    
    # 8: relation fields
    area_id = fields.Many2one(comodel_name='res.area', string='Area', help='')
    parent_id = fields.Many2one(comodel_name='res.branch', string='Parent Branch', help='')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', help='')
    kawil_id = fields.Many2one(comodel_name='hr.employee', string='Kepala Wilayah', domain=[('job_id.sales_force','=','am')])
    owner_id = fields.Many2one(comodel_name='hr.employee', string='Owner')
    kacab_id = fields.Many2one(comodel_name='hr.employee', string='Kepala Cabang', domain=[('job_id.sales_force','=','soh')])
    adh_id = fields.Many2one(comodel_name='hr.employee', string='Admin Head')
    kabeng_id = fields.Many2one(comodel_name='hr.employee', string='Kepala Bengkel')
    kasir_id = fields.Many2one(comodel_name='hr.employee', string='Kasir')

    # 10: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 12: override methods
    
    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        for record in self :
            name = record.name
            if record.code:
                name = "[%s] %s" % (record.code, name)
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('code', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()