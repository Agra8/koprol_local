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

class MasterJrfArf(models.Model):
    _name="master.jrf.arf"
    _description="Master JRF / ARF"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    type_form = fields.Selection(string='Type Form', selection=[('jrf','Job Request'),('arf','Access Request')])
    approval_default = fields.Selection(string='Default Approval',
    selection=[
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
        ])
    # Audit Trail

    # 8: Relational Fields
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            type_form = record.type_form
            if not record.name:
                name = '%s - %s' % (name,type_form)
            else:
                name = '%s - %s' % (record.name,record.type_form)
            res.append((record.id,name))
        return res            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('type_form',operator,name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()