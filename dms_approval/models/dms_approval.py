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

class MasterApproval(models.Model):
    _name="dms.approval"
    _description="DMS Master Approval"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')


    # Audit Trail

    # 8: Relational Fields
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    form_id = fields.Many2one(comodel_name='dms.approval.config', string='Form')
    line_ids = fields.One2many(comodel_name='dms.approval.line',inverse_name='approval_id',string="Approval Lines")
    
    # 9: methods
    @api.model
    def create(self, vals):
        vals['name'] = self.form_id.name

        return super(MasterApproval, self).create(vals)
    
    def write(self, vals):
        vals['name'] = self.form_id.name

        return super(MasterApproval, self).write(vals)

    def copy(self):
        raise Warning("Tidak dapat di duplicate !")
    
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            form_id = record.form_id.name
            if not record.name:
                name = '%s - %s' % (name,form_id)
            else:
                name = '%s - %s' % (record.name,record.form_id.name)
            res.append((record.id,name))
        return res            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('form_id',operator,name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()

class MasterApprovalLine(models.Model):
    _name="dms.approval.line"
    _description="Master Approval Line"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    code_approval = fields.Integer(string='Kode Approval')



    # Audit Trail

    # 8: Relational Fields
    group_id = fields.Many2one(comodel_name='res.groups', string='Groups')
    approval_id = fields.Many2one(comodel_name='dms.approval', string='Approval' )
    
    
    # 9: methods
    
    def copy(self):
        raise Warning("Tidak dapat di duplicate !")

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

