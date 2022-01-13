from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Business(models.Model):
    _name = 'eps.business'

    name = fields.Char(string='Name')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Name sudah digunakan !')
    ]