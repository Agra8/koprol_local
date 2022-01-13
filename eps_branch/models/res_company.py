from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    code = fields.Char(string='Code')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Code sudah digunakan !')
    ]