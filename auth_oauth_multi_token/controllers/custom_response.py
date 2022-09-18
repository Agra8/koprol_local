import json

from odoo.http import JsonRequest, Response, Root, request
from odoo.tools import date_utils
from odoo.service import security

from .response import Respapi


class JsonRequestPatch(JsonRequest):

    def _json_response(self, result=None, error=None):
        default_code = 200
        mime = 'application/json'
        response = {}
        if isinstance(result, Respapi):
            return result
        else:
            response = {
                'jsonrpc': '2.0',
                'id': self.jsonrequest.get('id')
            }
            if error is not None:
                response['error'] = error
            if result is not None:
                response['result'] = result

        body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop(
                'http_status', default_code) or default_code,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )
    
class RootPath(Root):
    def get_response(self, httprequest, result, explicit_session):
        if isinstance(result, Response) and result.is_qweb:
            try:
                result.flatten()
            except Exception as e:
                if request.db:
                    result = request.registry['ir.http']._handle_exception(e)
                else:
                    raise

        if isinstance(result, (bytes, str)):
            response = Response(result, mimetype='text/html')
        elif isinstance(result, Respapi):
            response = Response(json.dumps(result.data, default=date_utils.json_default), mimetype='application/json', status=result.code)
        else:
            response = result
    
        save_session = (not request.endpoint) or request.endpoint.routing.get('save_session', True)
        if not save_session:
            return response

        if httprequest.session.should_save:
            if httprequest.session.rotate:
                self.session_store.delete(httprequest.session)
                httprequest.session.sid = self.session_store.generate_key()
                if httprequest.session.uid:
                    httprequest.session.session_token = security.compute_session_token(httprequest.session, request.env)
                httprequest.session.modified = True
            self.session_store.save(httprequest.session)
        # We must not set the cookie if the session id was specified using a http header or a GET parameter.
        # There are two reasons to this:
        # - When using one of those two means we consider that we are overriding the cookie, which means creating a new
        #   session on top of an already existing session and we don't want to create a mess with the 'normal' session
        #   (the one using the cookie). That is a special feature of the Session Javascript class.
        # - It could allow session fixation attacks.
        if not explicit_session and hasattr(response, 'set_cookie'):
            response.set_cookie(
                'session_id', httprequest.session.sid, max_age=90 * 24 * 60 * 60, httponly=True)

        return response

Root.get_response = RootPath.get_response
JsonRequest._json_response = JsonRequestPatch._json_response
# HttpRequest.make_response = HttpRequestPatch.make_response
