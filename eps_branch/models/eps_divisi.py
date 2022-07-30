from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Divisi(models.Model):
    _name = "eps.divisi"
    _description = 'Divisi'

    def _get_company(self):
        res_user = self.env['res.users'].browse(self._uid)
        return res_user.company_id.id

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,default=_get_company)
    code = fields.Char(string='Code')
    tops_id = fields.Char('TOPS ID')
    
    @api.constrains('company_id','name')
    def _check_name(self):
        for record in self:
            division = self.search([('company_id','=',record.company_id.id),('name','=',record.name),('id','!=',record.id)])
            if division:
                raise ValidationError('Nama sudah pernah digunakan!')

    def init(self):
        self._cr.execute("""
            ALTER TABLE IF EXISTS eps_divisi 
            DROP CONSTRAINT IF EXISTS eps_divisi_name_unique
            
        """
        ) 