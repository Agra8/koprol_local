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
    sla_days = fields.Integer('SLA Approval Days')
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Nama Kategori tidak boleh ada yang sama.'),
        ('code_unique', 'unique(code)', 'Kode Kategori tidak boleh ada yang sama.')
    ] 

    @api.onchange('group_id')
    def _onchange_group(self):
        if self.group_id:
            self.matrix_sequence = 0
            self.limit = 0
            self.sla_days = 0