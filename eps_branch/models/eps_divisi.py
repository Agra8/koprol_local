from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Divisi(models.Model):
    _name = "eps.divisi"
    _description = 'Divisi'

    name = fields.Char(string='Name', required=True)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Nama Divisi tidak boleh ada yang sama.')
    ] 