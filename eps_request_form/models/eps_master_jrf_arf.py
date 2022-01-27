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
    _name="eps.master.jrf.arf"
    _description="Master JRF / ARF"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
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
    teams_id = fields.Many2one(comodel_name='eps.teams.master', string='Teams', domain="[('company_id', '=', company_id)]" )
    type_form_id = fields.Many2one(comodel_name='eps.request.form.type', string='Tipe Request')

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
    

class TypeRequest(models.Model):
    _name="eps.request.form.type"
    _description="Tipe dari request"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
        
    # Audit Trail

    # 8: Relational Fields
    master_jrf_ids = fields.One2many(comodel_name='eps.master.jrf.arf', string='Request Form', inverse_name='type_form_id')
    
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