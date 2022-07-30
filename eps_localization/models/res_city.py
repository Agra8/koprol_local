from odoo import models, fields, api

class City (models.Model):
    _name = "res.city"
    _description = "City"

    name = fields.Char('Nama Kabupaten',required=True)
    code = fields.Char('Code',size=128,required=True)
    state_id = fields.Many2one('res.country.state','Province',required=True)
    kecamatan_ids = fields.One2many('res.kecamatan','city_id','Kecamatan', readonly=True) 
    _sql_constraints = [
       ('code_unique', 'unique(code)', 'Kode Kabupaten tidak boleh ada yang sama.') 
    ]

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(City,self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(City, self).write(vals)

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
