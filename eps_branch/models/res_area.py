# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Area(models.Model):
    _inherit = "res.area"
    _description = 'Area'

    name = fields.Char(string='Code', required=True)
    description = fields.Char(string='Description', required=True)
    company_ids = fields.Many2many('res.company', string='Company')
    branch_ids = fields.Many2many('res.branch', domain="[('company_id','in', company_ids)]", string='Branches')

    _sql_constraints = [('code_unique', 'unique(name)', 'Code tidak boleh ada yang sama.')]
    
    def name_get(self,context=None):
        if context is None:
            context = {}
        res = []
        for record in self :
            tit = "[%s] %s" % (record.name, record.description)
            res.append((record.id, tit))
        return res

    @api.model
    def create(self, vals): 
        create = super(Area, self).create(vals)
        self.env['ir.rule'].clear_caches()
        self.clear_caches()
        return create

    def write(self, vals): 
        write = super(Area, self).write(vals)
        self.env['ir.rule'].clear_caches()
        self.clear_caches()
        return write

    def unlink(self):
        unlink = super(Area, self).unlink()
        self.env['ir.rule'].clear_caches()
        self.clear_caches()
        return unlink
