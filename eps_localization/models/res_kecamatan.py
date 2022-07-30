from odoo import models, fields, api

class Kecamatan (models.Model):
    _name = "res.kecamatan"
    _description = "Kecamatan"

    name = fields.Char('Kecamatan', required=True)
    city_id = fields.Many2one('res.city', string='City', required=True)
    code = fields.Char('Code',size=128,required=True)
    state_id = fields.Many2one(related='city_id.state_id',relation='res.country.state', readonly=True, string='Province',store=False)
    kelurahan_ids = fields.One2many('res.kelurahan','kecamatan_id',string='Kelurahan', readonly=True)
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Kode Kecamatan tidak boleh ada yang sama.')
    ] 

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Kecamatan,self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Kecamatan, self).write(vals)

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
