from email.policy import default
from urllib import request
from venv import create
from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_provider(self):
        self.oauth_provider_id = self.user_id.sudo().oauth_provider_id
            
    is_oauth = fields.Boolean('Oauth Login')
    work_email = fields.Char(readonly=False, related="user_id.oauth_uid", string='Work Email', store=True, tracking=True)
    oauth_provider_id = fields.Many2one('auth.oauth.provider', readonly=False, related="user_id.oauth_provider_id", string='OAuth Provider', domain="[('enabled','=',True)]", store=True, tracking=True)
    
    @api.model
    def create(self,vals):
        if(not self.user_id.oauth_uid):
            self.user_id.oauth_uid = self.work_email
        return super(HrEmployee,self).create(vals)

    def write(self,vals):
        if(not self.user_id.oauth_uid):
            self.user_id.oauth_uid = self.work_email
        return super(HrEmployee,self).write(vals)
