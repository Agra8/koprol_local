from odoo import fields, models, api
from odoo.exceptions import ValidationError

class KoprolSetting(models.Model):
    _name = 'eps.koprol.setting'

    default_company_vendor_approval_id = fields.Many2one('res.company', string='Default Company for Vendor Approval', required=True)
    default_branch_vendor_approval_id = fields.Many2one('res.branch', string='Default Branch for Vendor Approval', required=True)
    default_divisi_vendor_approval_id = fields.Many2one('eps.divisi', string='Default Division for Vendor Approval', required=True)
    default_company_initiatives_approval_id = fields.Many2one('res.company', string='Default Company for Vendor Approval', required=True)
    default_branch_initiatives_approval_id = fields.Many2one('res.branch', string='Default Branch for Vendor Approval', required=True)
    default_divisi_initiatives_approval_id = fields.Many2one('eps.divisi', string='Default Division for Vendor Approval', required=True)

    @api.constrains('default_company_vendor_approval_id','default_company_vendor_approval_id','default_company_vendor_approval_id')
    def _check_double_entries(self):
        for rec in self:
            existing = self.search([('id','!=',rec.id)])
            if existing:
                raise ValidationError('Hanya bisa input setting sekali! silahkan edit record yang sudah ada')
