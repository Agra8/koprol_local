# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ResUsers(models.Model):
    _inherit = 'res.users'

    area_id = fields.Many2one('res.area','Area',help='Area for this user.')
    branch_ids = fields.Many2many(string='Branches', related='area_id.branch_ids')
    area_id = fields.Many2one('res.area','Area',context={'user_preference':True},help='Area for this user.')
    branch_ids_show = fields.Many2many(related='area_id.branch_ids',string='Branches')
    area_id_show = fields.Many2one(related='area_id',string='Area',context={'user_preference':True},help='Area for this user.')
    
    @api.onchange('area_id')
    def _onchange_area(self):
        if self.area_id:
            self.company_ids = self.area_id.company_ids
    
    # def __init__(self, pool, cr):
    #     """ Override of __init__ to add access rights on
    #     store fields. Access rights are disabled by
    #     default, but allowed on some specific fields defined in
    #     self.SELF_{READ/WRITE}ABLE_FIELDS.
    #     """
    #     init_res = super(ResUsers, self).__init__(pool, cr)
    #     # duplicate list to avoid modifying the original reference
    #     self.SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
    #     self.SELF_WRITEABLE_FIELDS.append('area_id')
    #     self.SELF_WRITEABLE_FIELDS.append('branch_ids')
    #     # duplicate list to avoid modifying the original reference
    #     self.SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
    #     self.SELF_READABLE_FIELDS.append('area_id')
    #     self.SELF_READABLE_FIELDS.append('branch_ids')
    #     return init_res

    @api.model
    def create(self, vals): 
        create = super(ResUsers, self).create(vals)
        if vals.get('area_id',False):
            self.env['ir.rule'].clear_caches()
            self.clear_caches()
        return create

    def write(self, vals): 
        write = super(ResUsers, self).write(vals)
        if vals.get('area_id',False):
            self.env['ir.rule'].clear_caches()
            self.clear_caches()
        return write
