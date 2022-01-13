from odoo import models, fields, api

class Kelurahan (models.Model):
    _name = 'res.kelurahan'
    _description = 'DMS Kelurahan'

    name = fields.Char('Nama Kelurahan')
    kode_pos = fields.Char('Zip Code',size=10,required=True) 
    kecamatan_id = fields.Many2one('res.kecamatan','Kecamatan',required=True)
    city_id = fields.Many2one(related='kecamatan_id.city_id',relation='res.city',readonly=True, string='City')
    state_id = fields.Many2one(related='kecamatan_id.state_id', relation='res.country.state',readonly=True, string='Province')
    _sql_constraints = [
       ('code_unique', 'unique(kode_pos)', 'Kode POS tidak boleh ada yang sama.')  
    ]

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Kelurahan,self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Kelurahan, self).write(vals)

    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            tit = "[%s] %s" % (record.kode_pos, record.name)
            res.append((record.id, tit))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|',('name', operator, name),('kode_pos', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()
