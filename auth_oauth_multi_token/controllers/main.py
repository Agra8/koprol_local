# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import functools
import logging
from http.client import UNAUTHORIZED
from json_checker import Checker, MissKeyCheckerError

from odoo.http import request
from odoo import api, http, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo import registry as registry_get

from odoo.addons.auth_oauth.controllers.main import OAuthController as Oauth
from odoo.addons.web.controllers.main import set_cookie_and_redirect

from .definitions import *
from .response import Respapi

_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# helpers
#----------------------------------------------------------
def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        kw.pop('debug', False)
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)
    return wrapper
PREFIX = 'Bearer'

def get_token_from_bearer(header):
    bearer, _, token = header.partition(' ')
    if bearer != PREFIX:
        return '__Invalid Token'

    return token

def check_valid_token(func):
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
            validation = request.env['res.users'].sudo().verify_token(checktoken.user_id.oauth_provider_id.id, access_token)
            if validation != checktoken.user_id.oauth_uid:
                return Respapi.error(UNAUTHORIZED)
            return func(self, *args, **kwargs)
        except ValueError as ve:
            return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_MULTY)
        except Exception as e:
            return Respapi.error(UNAUTHORIZED, errorDescription=str(e))
    return wrap

class OauthProviderController(Oauth):
    @http.route('/oauth/signin', type='json', auth='public', methods=['POST'], csrf=False)
    def oauthsignin(self, **kw):
        expected_schema = {'access_token': str, 'device_id': str, 'device_type':str, 'p':int}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state
            dbname = 'koproldb'
            provider = state['p']
            context = state.get('c', {})
            registry = registry_get(dbname)
            with registry.cursor() as cr:
            
                env = api.Environment(cr, SUPERUSER_ID, context)
                (dbname, login, access_token) = env['res.users'].sudo().auth_oauth(provider, state)
                cr.commit()

                if access_token :
                    user = request.env['res.users'].sudo().search([('login','=',login)],limit=1)
                    if not user:
                        raise AccessDenied()
                    emp = request.env['hr.employee'].sudo().search([('user_id','=',user.id)],limit=1)

                    if not emp:
                        raise AccessDenied()
                       
                    # Successful response:
                    job = emp.job_id
                    response = Respapi.success(
                        {
                            'id': user.id,
                            'company_name': user.company_id.name if user.id else 'null',
                            'access_token': access_token,
                            'role_id':job.id,
                            'role':job.name,
                            'name':user.partner_id.name,
                            'display_name':user.partner_id.display_name,
                            'email':user.oauth_uid,
                        }
                    )
                    return response
        except AttributeError:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled." % (dbname,))
                url = "/web/login?oauth_error=1"
                return Respapi.error(errorDescription="auth_signup not installed")
        except AccessDenied:
            # oauth credentials not valid, user could be on a temporary session
            _logger.info('OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
            return Respapi.error(errorDescription='You do not have access to this database or your invitation has expired. Please ask for an invitation and be sure to follow the link in your invitation email.')
        except MissKeyCheckerError as ae:
            _logger.exception("Validation: %s" % str(ae))
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except Exception as e:
            # signup error
            _logger.exception("OAuth2: %s" % str(e))
            # url = "/web/login?oauth_error=2"
            return Respapi.error(code=UNAUTHORIZED, error=str(e.args[0]['code']) if 'code' in e.args[0] else "Error", errorDescription=str(e.args[0]['message']) if 'message' in e.args[0] else e)
        return set_cookie_and_redirect(url)

