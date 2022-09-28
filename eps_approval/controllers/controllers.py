from ast import literal_eval
import logging
from mimetypes import init

from odoo import http, _
from odoo.exceptions import MissingError
from odoo.http import request

from json_checker import MissKeyCheckerError

from ...eps_base_api.controllers.response import Respapi
from ...eps_base_api.controllers.definitions import API_VERSION
from ...eps_auth_oauth.controllers.check_token import AuthOauthCheckToken as auth

_logger = logging.getLogger(__name__)
version = API_VERSION

class EpsApproval(http.Controller):

    @http.route(f'{version}/approvals/version', auth='public', csrf=False)
    @auth.check_token
    def index(self, **kw):
        return version

    @http.route(f'{version}/approvals/dashboard', type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def dashboard(self, **params):
        try:

            conditions = [('model_id', '!=', False)]

            # search
            conditions.append(tuple(
                ['transaction_no', 'like', params['search']])) if "search" in params else False

            # filter
            conditions.append(tuple(['department_id', 'in', literal_eval(
                params['department_id'])]))if "department_id" in params else False
            conditions.append(tuple(['divisi_id', 'in', literal_eval(
                params['divisi_id'])])) if "divisi_id" in params else False
            conditions.append(tuple(['company_id', 'in', literal_eval(
                params['company_id'])])) if "company_id" in params else False
            # conditions.append(tuple(['branch_id','in',literal_eval(params['branch_id'])])) if "branch_id" in params else False

            # filter by session
            user = request.env['res.users'].browse(request.session.uid)
            branches = user.area_id.sudo().branch_ids
            conditions.append(
                tuple(['group_id', 'in', [group.id for group in user['groups_id']]]))
            conditions.append(
                tuple(['branch_id', 'in', [branch.id for branch in branches]]))

            # approval count
            conditions_approval = []
            conditions_approval.extend(conditions)
            conditions_approval.append(tuple(['state', 'in', ['IN']]))
            approval = request.env['eps.approval.transaction'].search_count(
                conditions_approval)
            # veto count
            conditions_veto = []
            conditions_veto.extend(conditions)
            conditions_veto.append(tuple(['state', 'in', ['WA']]))
            approval_veto = request.env['eps.approval.transaction'].search_count(
                conditions_veto)

            dashboard = {
                'approvals': approval,
                'veto': approval_veto
            }
            return Respapi.success(dashboard)
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/approvals', f'{version}/approvals/veto', f'{version}/approvals/history'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def list(self, **params):
        try:

            state = ['IN']
            if(request.httprequest.path == f'{version}/approvals/veto'):
                state = ['WA']

            conditions = [('model_id', '!=', False), ('state', 'in', state)]

            if(request.httprequest.path == f'{version}/approvals/history'):
                # TODO: history condition has not clear
                conditions = [('model_id', '!=', False), ('tanggal', '!=', False)]

            # pagination
            offset = int(params['offset']) if "offset" in params else 0
            limit = int(params['limit']) if "limit" in params else 10

            # order by
            order = params['order'] if "order" in params else 'tanggal desc'

            # search
            conditions.append(tuple(
                ['transaction_no', 'like', params['search']])) if "search" in params else False

            # filter
            conditions.append(tuple(['department_id', 'in', literal_eval(
                params['department_id'])]))if "department_id" in params else False
            conditions.append(tuple(['divisi_id', 'in', literal_eval(
                params['divisi_id'])])) if "divisi_id" in params else False
            conditions.append(tuple(['company_id', 'in', literal_eval(
                params['company_id'])])) if "company_id" in params else False
            # conditions.append(tuple(['branch_id','in',literal_eval(params['branch_id'])])) if "branch_id" in params else False

            # filter by session
            user = request.env['res.users'].browse(request.session.uid)
            branches = user.area_id.sudo().branch_ids
            conditions.append(
                tuple(['group_id', 'in', [group.id for group in user['groups_id']]]))
            conditions.append(
                tuple(['branch_id', 'in', [branch.id for branch in branches]]))
            approval = request.env['eps.approval.transaction'].search(
                conditions, offset=offset, limit=limit, order=order)
            list = [{
                'id': app.id,
                'transaction_id': app.transaction_id,
                'transaction_no': app.transaction_no if app.transaction_no else None,
                'company': {
                    'id': app.company_id.id,
                    'name': app.company_id.name,
                } if app.company_id else None,
                'branch': {
                    'id': app.branch_id.id,
                    'name': app.branch_id.name
                } if app.branch_id else None,
                'divisi': {
                    'id': app.divisi_id.id,
                    'name': app.divisi_id.name
                } if app.divisi_id else None,
                'department': {
                    'id': app.department_id.id,
                    'name': app.department_id.name
                } if app.department_id else None,
                'value': app.value,
                'date': app.tanggal.strftime("%Y-%m-%d %H:%M:%S") if app.tanggal else None,
                'state': app.state,
                'route': {
                    'endpoint_detail': f'{version}/{(app.model_id.name).lower()}/{app.transaction_id}?apvid={app.id}' if app.model_id.name else f'{version}/approval?apvid={app.id}',
                    'screen': f'/{(app.model_id.name).lower()}' if app.model_id.name else '/approval'
                }
            } for app in approval]
            return Respapi.success(list)
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/approval/<id>'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def detail(self, id=None, **_):
        try:
            # one of approval transaction
            approval_transaction = request.env['eps.approval.transaction'].suspend_security(
            ).browse(int(id))

            if not approval_transaction.transaction_id:
                raise MissingError(
                    'Transaction does not exist or has been deleted')

            # all of approval transaction with transaction_id filter
            approval_line = request.env['eps.approval.transaction'].suspend_security(
            ).search([('transaction_id', '=', approval_transaction.transaction_id)])

            detail = {
                'transaction_id': approval_transaction.transaction_id,
                'transaction_no': approval_transaction.transaction_no,
                'tanggal': approval_transaction.tanggal.strftime("%Y-%m-%d %H:%M:%S") if approval_transaction.tanggal is not False else None,

                'company': {
                    'id': approval_transaction.company_id.id,
                    'name': approval_transaction.company_id.name,
                } if approval_transaction.company_id else None,
                'branch': {
                    'id': approval_transaction.branch_id.id,
                    'name': approval_transaction.branch_id.name
                } if approval_transaction.branch_id else None,
                'divisi': {
                    'id': approval_transaction.divisi_id.id,
                    'name': approval_transaction.divisi_id.name
                } if approval_transaction.divisi_id else None,
                'department': {
                    'id': approval_transaction.department_id.id,
                    'name': approval_transaction.department_id.name
                } if approval_transaction.department_id else None,

                'value': approval_transaction.value,
                'state': approval_transaction.state,
                'approval': [
                    {
                        'id': approval.id,
                        'matrix_sequence': approval.matrix_sequence,
                        'group': {
                            'id': approval.group_id.id,
                            'name': approval.group_id.name,
                        },
                        'tanggal': approval.tanggal if approval.tanggal else None,
                        'user': {
                            'id': approval.user_id.id,
                            'name': approval.user_id.name,
                        } if approval.user_id else None,
                        'state': approval.state,
                        'limit': approval.limit
                    } for approval in approval_line
                ]
            }

            return Respapi.success(detail)
        except MissKeyCheckerError as ae:
            _logger.exception("Validation: %s, %s" %
                              (str(request.httprequest.path), str(ae)))
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            return Respapi.error(errorDescription=str(me))
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

