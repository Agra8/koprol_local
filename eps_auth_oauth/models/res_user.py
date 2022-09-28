from http.client import UNAUTHORIZED
import json
import requests

from ...eps_auth_oauth.controllers.definitions import ERR_TOKEN_NOT_FOUND_DATABASE
from ...eps_base_api.controllers.response import Respapi

from odoo.exceptions import AccessDenied, UserError
from odoo import api,  models

class ResUsers(models.Model):
    _inherit = "res.users"
    
    @api.model
    def _auth_oauth_rpc(self, endpoint, access_token):
        if 'graph.microsoft.com' in endpoint:
            return requests.get(
                endpoint, headers={'Authorization': 'Bearer {}'.format(access_token)}
            ).json()
        return super()._auth_oauth_rpc(endpoint, access_token)
    
    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        # oauth_uid = validation['user_id']
        email =  validation['email'] if 'email' in validation else validation['mail']
        oauth_user = self.search([("oauth_uid", "=", email), ('oauth_provider_id', '=', provider)])
        if not oauth_user:
            raise AccessDenied()
        assert len(oauth_user) == 1
        oauth_user.write({'oauth_access_token': params['access_token']})
        return oauth_user.login
       

    # is verify (True/False)
    def verify_token(self, access_token):

        user = self.env['res.users'].sudo().search(
                    [('oauth_access_token', '=', access_token)], order='id DESC', limit=1)

        if not user:
            return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_DATABASE)
        user.ensure_one()

        # validation provider
        validation = super()._auth_oauth_validate(user.oauth_provider_id.id, access_token)
        
        if not validation.get('user_id'):
            # Workaround: facebook does not send 'user_id' in Open Graph Api
            if validation.get('id'):
                validation['user_id'] = validation['id']
            else:
                raise AccessDenied()
        
        email = validation['mail'] if 'mail' in validation else validation['email'] if 'email' in validation else False
        return user.oauth_access_token if email == user.oauth_uid else False

    # old
    # def verify_token(self, provider, access_token, oauth_uid):

    #     validation = super()._auth_oauth_validate(provider, access_token)
    #     # required check
    #     if not validation.get('user_id'):
    #         # Workaround: facebook does not send 'user_id' in Open Graph Api
    #         if validation.get('id'):
    #             validation['user_id'] = validation['id']
    #         else:
    #             raise AccessDenied()
        
    #     email = validation['mail'] if 'mail' in validation else validation['email'] if 'email' in validation else False

    #     return email == oauth_uid
        

    