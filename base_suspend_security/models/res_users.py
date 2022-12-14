# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models

from ..base_suspend_security import BaseSuspendSecurityUid


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def _browse(cls, env, ids, prefetch_ids):
        """be sure we browse ints, ids laread is normalized"""
        return super(ResUsers, cls)._browse(env ,
            tuple([
                i if not isinstance(i, BaseSuspendSecurityUid)
                else super(BaseSuspendSecurityUid, i).__int__()
                for i in ids
            ]), prefetch_ids=prefetch_ids)
