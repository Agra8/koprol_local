# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import functools
import logging
from http.client import UNAUTHORIZED
from json_checker import Checker, MissKeyCheckerError
import werkzeug.urls
import werkzeug.utils

from odoo import api, http, SUPERUSER_ID, _
from odoo import registry as registry_get
from odoo.http import request
from odoo.exceptions import AccessDenied

from odoo.addons.web.controllers.main import set_cookie_and_redirect, login_and_redirect
from odoo.addons.auth_oauth.controllers.main import OAuthController as Oauth
from odoo.addons.web.controllers.main import set_cookie_and_redirect
from ...eps_base_api.controllers.response import Respapi

from .definitions import *

_logger = logging.getLogger(__name__)

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
                       
                    job = emp.job_id
                    # TODO
                    resp = login_and_redirect(*(dbname, login, access_token), redirect_url='/')
                    # Since /web is hardcoded, verify user has right to land on it
                    if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                        resp.location = '/'

                    # Successful response:
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