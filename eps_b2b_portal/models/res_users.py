from odoo import models, fields, api
import os

class Users(models.Model):
    _inherit = "res.users"
    
    api_client_id = fields.Char('Client ID')
    api_key_id = fields.Char('API Key')
    portal_partner_ids = fields.One2many('eps.portal.user.partner','user_id','Partners')
    is_user_b2b_portal = fields.Boolean('User B2b Portal ?')
    

   
    def action_generate_api_key(self):
        code = os.urandom(24).encode('hex')
        code2 = os.urandom(24).encode('hex')
        self.write({
            'api_key_id':code,
            'api_client_id':code2
        })

    @api.onchange('api_client_id')
    def onchange_apiclientId(self):
        self.api_key_id = False


class PortalUserPartner(models.Model):
    _name = "eps.portal.user.partner"

    user_id = fields.Many2one('res.users','User')
    partner_id = fields.Many2one('res.partner','Partner',domain="[('customer_rank','=',1)]")

    _sql_constraints = [('user_partner_uniqe', 'unique(user_id,partner_id)', 'Partner tidak boleh duplikat !')]