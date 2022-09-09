# Copyright 2016 Florent de Labarre
# Copyright 2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from datetime import datetime, timedelta
from odoo.exceptions import AccessDenied, UserError
import uuid
import requests

from odoo import api, exceptions, fields, models
from odoo.addons import base

base.models.res_users.USER_PRIVATE_FIELDS.append('oauth_master_uuid')


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_rpc(self, endpoint, access_token):
        if 'graph.microsoft.com' in endpoint:
            return requests.get(
                endpoint, headers={'Authorization': 'Bearer {}'.format(access_token)}
            ).json()
        return super()._auth_oauth_rpc(endpoint, access_token)

    def _generate_oauth_master_uuid(self):
        return uuid.uuid4().hex

    oauth_access_token_ids = fields.One2many(
        comodel_name='auth.oauth.multi.token',
        inverse_name='user_id',
        string='OAuth tokens',
        copy=False,
        readonly=True,
        groups='base.group_system',
    )
    oauth_access_max_token = fields.Integer(
        string='Max number of simultaneous connections', default=10, required=True
    )
    oauth_master_uuid = fields.Char(
        string='Master UUID',
        copy=False,
        readonly=True,
        required=True,
        default=lambda self: self._generate_oauth_master_uuid(),
    )

    @property
    def multi_token_model(self):
        return self.env["auth.oauth.multi.token"]

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """Override to handle sign-in with multi token."""

        email =  validation['email'] if 'email' in validation else validation['mail']
        device_id =  params['device_id'] if 'device_id' in params else f'web_{email}'
        device_type =  params['device_type'] if 'device_type' in params else 'web'

        # Lookup for user by oauth uid and provider
        user = self.search([('oauth_uid', '=', email), ('oauth_provider_id', '=', provider)])

        if not user:
            raise exceptions.AccessDenied()
        user.ensure_one()

        # search for device_id
        #   if device_id:
        #     if device_id.user_id = user.id or (device_id.user_id != user.id and (today - device_id.logout_on) > 24 jam):
        #       replace access_token
        #     else:
        #       raise error
        #   else:
        #     insert access_token

        # search device id
        multi_token = self.multi_token_model.sudo().search([('device_id', '=', device_id)])
        # device found
        if multi_token:
            isFound = False
            # when found > 1
            for mt in multi_token:
                if mt.user_id.id == user.id:
                    mt.write({'oauth_access_token': params['access_token']})
                    isFound = True
                    break
                # logout on null, logout by system
                elif not mt.logout_on:
                    mt.write({'device_id': f'LOGOUT_BY_SYSTEM_{mt.device_id}'})
                    self.multi_token_model.sudo().create({
                        'oauth_access_token':params['access_token'],
                        'active_token': True,
                        'device_id':device_id,
                        'device_type':device_type,
                        'user_id':user.id
                    })
                    isFound = True
                    break
                # last login < 24 hours
                elif datetime.now() - mt.logout_on >= timedelta(days=1):
                    self.multi_token_model.sudo().create({
                        'oauth_access_token':params['access_token'],
                        'active_token': True,
                        'device_id':device_id,
                        'device_type':device_type,
                        'user_id':user.id
                    })
                    isFound = True
                    break

            if not isFound:
                raise exceptions.AccessError('Cant login new user, waiting 24hours after last logout or please login with your last account')
        else:
            self.multi_token_model.sudo().create({
                'oauth_access_token':params['access_token'],
                'active_token': True,
                'device_id':device_id,
                'device_type':device_type,
                'user_id':user.id
            })
        return user.login

    def action_oauth_clear_token(self):
        """Inactivate current user tokens."""
        self.mapped("oauth_access_token_ids")._oauth_clear_token()
        for res in self:
            res.oauth_master_uuid = self._generate_oauth_master_uuid()

    @api.model
    def _check_credentials(self, password, env):
        """Override to check credentials against multi tokens."""
        try:
            return super()._check_credentials(password, env)
        except exceptions.AccessDenied:
            res = self.multi_token_model.sudo().search(
                [
                    ('user_id', '=', self.env.uid),
                    ('oauth_access_token', '=', password),
                    ('active_token', '=', True),
                ]
            )
            if not res:
                raise

    def _get_session_token_fields(self):
        res = super()._get_session_token_fields()
        res.remove('oauth_access_token')
        return res | {'oauth_master_uuid'}

    def verify_token(self, provider, access_token):
        validation = super()._auth_oauth_validate(provider, access_token)
        # required check
        if not validation.get('user_id'):
            # Workaround: facebook does not send 'user_id' in Open Graph Api
            if validation.get('id'):
                validation['user_id'] = validation['id']
            else:
                raise AccessDenied()
        
        return validation['mail'] if 'mail' in validation else validation['email'] if 'email' in validation else False


