
import functools
import logging
from http.client import UNAUTHORIZED
from mimetypes import init

from odoo.http import request, Controller
from ...eps_base_api.controllers.response import Respapi

from .definitions import *

_logger = logging.getLogger(__name__)
PREFIX = 'Bearer'

def get_token_from_bearer(header):
    bearer, _, token = header.partition(' ')
    if bearer != PREFIX:
        return '__Invalid Token'

    return token

class AuthOauthCheckToken(Controller):

    def check_token(func):
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            access_token = get_token_from_bearer(request.httprequest.headers['Authorization']) if 'Authorization' in request.httprequest.headers else False
            if not access_token:
                return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_HEADER)
            try:
                
                # verification token to provider
                token = request.env['res.users'].sudo().verify_token(request.httprequest.headers['device_id'], access_token)
                
                if not token:
                    return Respapi.error(UNAUTHORIZED)
                    
                # create session
                request.session.uid = token.user_id.id
                request.uid = token.user_id.id

                return func(self, *args, **kwargs)
            except ValueError as ve:
                return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_MULTY)
            except Exception as e:
                return Respapi.error(code=UNAUTHORIZED, error=str(e.args[0]['code']) if 'code' in e.args[0] else "Error", errorDescription=str(e.args[0]['message']) if 'message' in e.args[0] else e)
        return wrap

    # def check_token(func):
    #     @functools.wraps(func)
    #     def wrap(self, *args, **kwargs):

    #         access_token = get_token_from_bearer(request.httprequest.headers['Authorization']) if 'Authorization' in request.httprequest.headers else False
    #         if not access_token:
    #             return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_HEADER)
    #         try:
    #             user = request.env['res.users'].sudo().search(
    #                 [('oauth_access_token', '=', access_token)], order='id DESC', limit=1)

    #             if not user:
    #                 return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_DATABASE)

    #             validation = request.env['res.users'].sudo().verify_token(user.oauth_provider_id.id, access_token, user.oauth_uid)
    #             if not validation:
    #                 return Respapi.error(UNAUTHORIZED)
                
    #             # create session
    #             request.session.uid = user.id
    #             request.uid = user.id
                
    #             return func(self, *args, **kwargs)
    #         except ValueError as ve:
    #             return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_MULTY)
    #         except Exception as e:
    #             return Respapi.error(code=UNAUTHORIZED, error=str(e.args[0]['code']) if 'code' in e.args[0] else "Error", errorDescription=str(e.args[0]['message']) if 'message' in e.args[0] else e)
    #     return wrap