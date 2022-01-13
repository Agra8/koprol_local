#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from typing import Sequence
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import Warning

# 5: local imports

# 6: Import of unknown third party lib

class MasterTypeRequest(models.Model):
    _name="master.type.request"
    _description="Master Tipe Request"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    # Audit Trail

    # 8: Relational Fields
    approval_id = fields.Many2one(comodel_name='dms.approval', string='Default Approval')
    # TODO: create TIM / company fields many2one
    company_id = fields.Many2one(comodel_name='res.company', string='Company')

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if not record.name:
                name = '%s' % (name)
            else:
                name = '%s' % (record.name)
            res.append((record.id,name))
        return res            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = [('name', operator, name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()