from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    code = fields.Char(string='Code')
    business_id = fields.Many2one('eps.business','Business')
    tops_id = fields.Char('TOPS ID')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Code sudah digunakan !')
    ]