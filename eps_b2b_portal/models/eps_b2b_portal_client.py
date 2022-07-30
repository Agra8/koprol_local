from odoo import models, fields, api
from odoo.exceptions import Warning, ValidationError
from datetime import datetime, timedelta
import os

class B2bPortalClient(models.Model):
    _name = "eps.b2b.portal.client"
    _rec_name = "user_id"

    user_id = fields.Many2one('res.users','User',domain="[('is_user_b2b_portal','=',True)]")
    api_client_id = fields.Char('Client ID',related="user_id.api_client_id",readonly=True)
    api_key_id = fields.Char('API Key',related="user_id.api_key_id",readonly=True)
    partner_ids = fields.One2many('eps.b2b.portal.client.partner','client_id')

    username = fields.Char('Username')
    password = fields.Char('Password')
    
    _sql_constraints = [('user_uniqe', 'unique(user_id)', 'User tidak boleh duplikat !')]

    @api.model
    def create(self,vals):
        # if not vals.get('partner_ids'):
        #     raise Warning('Partners tidak boleh kosong !')
        if vals.get('client_id'):
            code = os.urandom(24).encode('hex')
            vals['secret_id'] = code
        return super(B2bPortalClient,self).create(vals)
    
    
    def write(self,vals):
        write = super(B2bPortalClient,self).write(vals)
        # if not self.partner_ids:
        #     raise Warning('Partners tidak boleh kosong !')
        return write

    
    def action_generate_secret(self):
        self.user_id.sudo().action_generate_api_key()

    def action_b2b_portal_client(self):
        cek_group = self.env['res.users'].has_group('eps_b2b_portal.group_eps_b2b_portal_client_allow_read')
        domain = []
        tree_id = self.env.ref('eps_b2b_portal.view_eps_b2b_portal_client_tree').id
        form_id = self.env.ref('eps_b2b_portal.view_eps_b2b_portal_client_form').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Client',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'eps.b2b.portal.client',
            'domain': domain,
            'views': [(tree_id, 'tree'), (form_id, 'form')]
        }

    # @api.onchange('user_id')
    # def onchange_user(self):
    #     partner_ids = []
    #     if self.user_id:
    #         partners = False
    #         partners = [p.partner_id for p in self.user_id.area_id.branch_ids]
    #         # if not partners:
    #         #     warning  = {'title': 'Perhatian !','message':'Partners list tidak ada !'}
    #         #     self.user_id = False
    #         #     return {'warning':warning}
    #         for partner in partners:
    #             if not partner.client_id:
    #                 partner_ids.append([0,False,{
    #                     'partner_id':partner.id    
    #                 }])
    #     self.partner_ids = partner_ids

class B2bPortalClientPartner(models.Model):
    _name = "eps.b2b.portal.client.partner"

    client_id = fields.Many2one('eps.b2b.portal.client','Client ID',ondelete='cascade')
    partner_id = fields.Many2one('res.partner','Partner',domain="[('client_id','=',False)]")

    @api.model
    def create(self,vals):
        create = super(B2bPortalClientPartner,self).create(vals)
        if create.partner_id:
            create.partner_id.client_id = create.client_id

    
    def unlink(self):
        for me in self:
            me.partner_id.client_id = False
        return super(B2bPortalClientPartner,self).unlink()

class Partner(models.Model):
    _inherit = "res.partner"

    client_id = fields.Many2one('eps.b2b.portal.client')
