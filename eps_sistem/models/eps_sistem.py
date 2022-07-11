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

class EpsTeamsMaster(models.Model):
    _name="eps.sistem.master"
    _description="eps Master Sistem"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    
    # Audit Trail

    # 8: Relational Fields
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    
    def copy(self):
        raise Warning("Data Tidak dapat di duplicate !")

    def unlink(self):
        raise Warning("Data Tidak dapat di hapus !")

    def eps_sistem_view(self):
        name = "Master Sistem"
        tree_id = self.env.ref('eps_sistem.eps_sistem_tree_view').id
        form_id = self.env.ref('eps_sistem.eps_sistem_form_view').id
        search_id = self.env.ref('eps_sistem.eps_sistem_search_view').id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'eps.sistem.master',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'readonly_by_pass': 1
            }
        }
      
    
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            company_id = record.company_id.name
            if not record.name:
                name = '%s - %s' % (name,company_id)
            else:
                name = '%s - %s' % (record.name, record.company_id.name)
            res.append((record.id,name))
        return res            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = [('name', operator, name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()