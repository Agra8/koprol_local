from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import time
import pytz
from pytz import timezone

class Partner(models.Model):
    _inherit = "res.partner"

    def _get_default_branch(self):
        branch_ids = False
        branch_ids = self.env.user.branch_ids
        if branch_ids and len(branch_ids) == 1 :
            return branch_ids[0].id
        return False

    default_code = fields.Char(string='Default Code')
    branch_id = fields.Many2one('res.branch', default=_get_default_branch, string='Branch',index=True)
    is_branch = fields.Boolean()
    