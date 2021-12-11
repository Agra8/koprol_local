#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Partner(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods
    
    # 8: fields
    default_code = fields.Char(string='Default Code', index=True)
    is_branch = fields.Boolean(string='Is Branch')
    is_md = fields.Boolean('Is Main Dealer')
    
    # 8: relation fields
    branch_id = fields.Many2one(comodel_name='res.branch', string='Branch')