from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    _inherit = "product.category"

    proposal_categ_id = fields.Many2one('eps.category', string='Proposal Category')

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    initiatives_line_id = fields.Many2one('eps.initiatives.line', string='Initiatives Lines')
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives')