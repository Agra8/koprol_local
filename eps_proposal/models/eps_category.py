from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Category(models.Model):
    _name = "eps.category"
    _description = 'Category'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    group_id = fields.Many2one('res.groups', string='Approval Group')
    matrix_sequence = fields.Integer('Sequence')
    limit = fields.Float('Limit')
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Nama Kategori tidak boleh ada yang sama.'),
        ('code_unique', 'unique(code)', 'Kode Kategori tidak boleh ada yang sama.')
    ] 