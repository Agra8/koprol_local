# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import functools
from http.client import UNAUTHORIZED

from odoo.http import request
from odoo.addons.eps_base_api.controllers.response import Respapi
from odoo.addons.eps_auth_oauth.controllers.controllers import get_token_from_bearer, EpsAuthOauth as Auth

from .definitions import *

class AuthOauthMulti(Auth):
    def check_valid_token_multi(func):
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):

            access_token = get_token_from_bearer(request.httprequest.headers['Authorization']) if 'Authorization' in request.httprequest.headers else False
            if not access_token:
                return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_HEADER)
            try:
                checktoken = request.env['auth.oauth.multi.token'].sudo().search([('oauth_access_token', '=', access_token)])
                if not checktoken:
                    return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_DATABASE)
                checktoken.ensure_one()

                # verification token to provider
                validation = request.env['res.users'].sudo().verify_token(checktoken.user_id.oauth_provider_id.id, access_token, checktoken.user_id.oauth_uid)
                
                if not validation:
                    return Respapi.error(UNAUTHORIZED)

                # import ipdb; ipdb.set_trace()
                # create session
                request.session.uid = checktoken.user_id.id
                request.uid = checktoken.user_id.id

                return func(self, *args, **kwargs)
            except ValueError as ve:
                return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_MULTY)
            except Exception as e:
                return Respapi.error(code=UNAUTHORIZED, error=str(e.args[0]['code']) if 'code' in e.args[0] else "Error", errorDescription=str(e.args[0]['message']) if 'message' in e.args[0] else e)
        return wrap

Auth.check_token = AuthOauthMulti.check_valid_token_multi