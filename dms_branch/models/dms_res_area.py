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

    _inherit = "res.area"
    _description = "Res Area"
    _order = "name desc"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    branch_ids = fields.Many2many(comodel_name='res.branch', string='Branchs', help="")

    # 10: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods