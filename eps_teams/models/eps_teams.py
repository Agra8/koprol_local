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
    _name="eps.teams.master"
    _description="eps Master Teams"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    
    # Audit Trail

    # 8: Relational Fields
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    teams_line_ids = fields.One2many(comodel_name='eps.teams.line', inverse_name='teams_id' )

    
    def copy(self):
        raise Warning("Data Tidak dapat di duplicate !")

    def unlink(self):
        raise Warning("Data Tidak dapat di hapus !")

    def eps_teams_view(self):
        name = "Master Teams"
        tree_id = self.env.ref('eps_teams.eps_teams_tree_view').id
        form_id = self.env.ref('eps_teams.eps_teams_form_view').id
        search_id = self.env.ref('eps_teams.eps_teams_search_view').id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'eps.teams.master',
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

class EpsTeamsLine(models.Model):
    _name="eps.teams.line"
    _description="eps Teams Line"

    # 7: defaults methods
   
    # 8: fields
    name = fields.Char(string='Name')
    # Audit Trail

    # 8: Relational Fields
    teams_id = fields.Many2one(comodel_name='eps.teams.master', string='Teams')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    job_id = fields.Many2one(comodel_name='hr.job', string='Job', compute='_change_job_name')

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
    
    @api.onchange('employee_id')
    def _change_job_name(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = [('name', operator, name)] + args
        categories = self.search(args,limit=limit)
        return categories.name_get()