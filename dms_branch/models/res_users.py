#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ResUsers(models.Model):
    _inherit = "res.users"

    # 7: defaults methods
    
    # 8: fields
    
    # 9: relation fields

    area_id = fields.Many2one(comodel_name='res.area', string='Area', context={'user_preference': True}, help='')
    branch_ids = fields.Many2many(comodel_name='res.branch', string='Dealers',related='area_id.branch_ids')

    # 10: constraints & sql constraints
    @api.onchange('area_id')
    def onchange_area(self):
        self.clear_caches()
        print('\n\n Cache Cleared \n\n')