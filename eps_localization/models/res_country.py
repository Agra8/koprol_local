from odoo import models, fields, api

class Country(models.Model):
    _inherit = "res.country"

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Country,self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Country, self).write(vals)
