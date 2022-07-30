from odoo import models, fields, api

class CountryState(models.Model):
    _inherit = "res.country.state"
    
    code = fields.Char('Code',size=7)
    city_ids = fields.One2many('res.city', 'state_id', string='City', readonly=True)

    _sql_constraints = [
       ('code_unique', 'unique(code)', 'Kode State tidak boleh ada yang sama.')  
    ] 
    
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(CountryState,self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(CountryState, self).write(vals)

    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            tit = "[%s] %s" % (record.code, record.name)
            res.append((record.id, tit))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|',('name', operator, name),('code', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()
