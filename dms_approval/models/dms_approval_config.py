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

class MasterApprovalConfig(models.Model):
    _name="dms.approval.config"
    _description="Dms Master Approval Config"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    form_id = fields.Many2one(comodel_name='ir.model', string='Form')
    type_id = fields.Many2one(comodel_name='dms.approval.type', string='Type')

    # Audit Trail

    # 8: Relational Fields
    
    def copy(self):
        raise Warning("Data Tidak dapat di duplicate !")

    def unlink(self):
        raise Warning("Data Tidak dapat di hapus !")
    
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            type_id = record.type_id.name
            if not record.name:
                name = '%s - %s' % (name,type_id)
            else:
                name = '%s - %s' % (record.name, record.type_id.name)
            res.append((record.id,name))
        return res            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('type_id',operator,name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()
    
    def dms_approval_config_view(self):
        name = "Master Approval Config"
        tree_id = self.env.ref('dms_approval.dms_approval_config_view_tree').id
        form_id = self.env.ref('dms_approval.dms_approval_config_view_form').id
        search_id = self.env.ref('dms_approval.dms_approval_config_search').id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'dms.approval.config',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'readonly_by_pass': 1
            }
        }


class MasterApprovalType(models.Model):
    _name="dms.approval.type"
    _description="Dms Master type Approval"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    # Audit Trail

    # 8: Relational Fields

    def copy(self):
        raise Warning("Tidak dapat di duplicate !")

    def unlink(self):
        raise Warning("Tidak dapat di hapus !")
    
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