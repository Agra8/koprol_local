#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ResArea(models.Model):
    _name = "res.area"
    _description = "Res Area"
    _order = "name desc"

    # 7: defaults methods

    # 8: fields

    name = fields.Char(required=True, string='Name', help='')
    code = fields.Char(string='Code', help='')
    description = fields.Char(string='Description', help='')

    # 10: methods
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            code = record.code
            if not record.name:
                name = '%s - %s' % (name,code)
            else:
                name = '%s - %s' % (record.name,record.code)
            res.append((record.id,name))
        return res            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('code',operator,name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()