
import logging

from odoo import http, _, exceptions
from odoo.exceptions import MissingError
from odoo.http import request

from json_checker import Checker, MissKeyCheckerError

from ...eps_base_api.controllers.response import Respapi
from ...eps_base_api.controllers.definitions import API_VERSION
from ...eps_auth_oauth.controllers.check_token import AuthOauthCheckToken as auth

_logger = logging.getLogger(__name__)
version = API_VERSION


class EpsProposal(http.Controller):

    @http.route([f'{version}/proposals'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def list(self, id=None, **params):
        try:

            # pagination
            offset = int(params['offset']) if "offset" in params else 0
            limit = int(params['limit']) if "limit" in params else 10

            # order by
            order = params['order'] if "order" in params else 'date desc, id asc'

            # filter by session
            user = request.env['res.users'].browse(request.session.uid)
            branches = user.area_id.sudo().branch_ids
            conditions = [
                (['branch_id', 'in', [branch.id for branch in branches]])]

            # proposal list
            proposals = request.env['eps.proposal'].search(
                conditions, limit=limit, offset=offset, order=order)

            list = [{
                    'id': proposal.id,
                    'name': proposal.name,
                    'nama_proposal': proposal.nama_proposal,
                    'tanggal': proposal.date.strftime("%Y-%m-%d %H:%M:%S") if proposal.date else None,
                    'total': proposal.total,
                    'branch': {
                        'id': proposal.branch_id.id,
                        'name': proposal.branch_id.name,
                    } if proposal.branch_id else None,
                    'company': {
                        'id': proposal.company_id.id,
                        'name': proposal.company_id.name,
                    } if proposal.company_id else None,
                    'divisi': {
                        'id': proposal.divisi_id.id,
                        'name': proposal.divisi_id.name
                    } if proposal.divisi_id else None,
                    'department': {
                        'id': proposal.department_id.id,
                        'name': proposal.department_id.name
                    } if proposal.department_id else None,
                    } for proposal in proposals]

            return Respapi.success(list)
        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            return Respapi.error(errorDescription=str(me))
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/proposal/<id>'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def detail(self, id=None, **params):
        try:
            # user
            # user = request.env['res.users'].browse(request.session.uid)

            # approval transaction
            approval = request.env['eps.approval.transaction'].browse(
                int(params['apvid'])) if "apvid" in params else False

            # proposal detail
            proposal = request.env['eps.proposal'].browse(int(id))

            # approval line proposal (id 507)
            approval_line = request.env['eps.approval.transaction'].search(
                [('transaction_id', '=', int(id)),('model_id','=',507)], order="id asc")

            # proposal category line
            proposal_category = request.env['eps.proposal.line'].search(
                [('proposal_id', '=', int(id))])

            # product line
            proposal_product = request.env['eps.proposal.product.line'].search(
                [('proposal_id', '=', int(id))])

            canAction = approval.state in ["IN", "WA"] if approval else False
            detail = {
                'id': proposal.id,
                'name': proposal.name,
                'nama_proposal': proposal.nama_proposal,
                'tanggal': proposal.date.strftime("%Y-%m-%d %H:%M:%S") if proposal.date is not False else None,
                'latar_belakang': proposal.latar_belakang,
                'sasaran_tujuan': proposal.sasaran_tujuan,
                'branch': {
                    'id': proposal.branch_id.sudo().id,
                    'name': proposal.branch_id.sudo().name,
                } if proposal.branch_id else None,
                'company': {
                    'id': proposal.company_id.id,
                    'name': proposal.company_id.name,
                } if proposal.company_id else None,
                'divisi': {
                    'id': proposal.divisi_id.id,
                    'name': proposal.divisi_id.name
                } if proposal.divisi_id else None,
                'department': {
                    'id': proposal.department_id.id,
                    'name': proposal.department_id.name
                } if proposal.department_id else None,
                'type': proposal.type,
                'pic': proposal.employee_id.name,
                'pic_contact': proposal.employee_id.mobile_phone if proposal.employee_id.mobile_phone else None,
                'state': proposal.state,
                'category_line': [
                    {
                        'id': category.id,
                        'price': category.price,
                        'name': category.categ_id.name,
                        'reserved_amount': category.reserved_amount,
                        'file': category.filename_penawaran if category.filename_penawaran else None,
                    } for category in proposal_category
                ],
                'product_line': [
                    {
                        'id': product.id,
                        'name': product.product_id.product_tmpl_id.name,
                        'supplier': {
                            'id': product.supplier_id.id,
                            'name': product.supplier_id.name
                        } if product.supplier_id else None,
                        'qty': product.quantity,
                        'price_unit': product.price_unit,
                        'price_total': product.price_total
                    } for product in proposal_product
                ],
                'approval_line': [
                    {
                        'id': approval.id,
                        'matrix_sequence': approval.matrix_sequence,
                        'group': {
                            'id': approval.group_id.id,
                            'name': approval.group_id.name,
                        } if approval.group_id else None,
                        'tanggal': approval.tanggal if approval.tanggal else None,
                        'user': {
                            'id': approval.user_id.id,
                            'name': approval.user_id.name,
                        } if approval.user_id else None,
                        'state': approval.state,
                        'limit': approval.limit,
                        'is_end': False if index == len(approval_line) - 1 else approval_line[index].limit > approval_line[index+1].limit
                    } for index, approval in enumerate(approval_line)
                ],
                'action': {
                    'approve': canAction,
                    'cancel': canAction,
                    'reject': canAction
                }
            }

            return Respapi.success(detail)
        except MissKeyCheckerError as ae:
            _logger.exception("Validation: %s, %s" %
                              (str(request.httprequest.path), str(ae)))
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/proposal/approve'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def approve(self, **_):
        expected_schema = {'id': int}
        try:
            state = request.jsonrequest

            # required request scheme
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # proposal detail
            proposal = request.env['eps.proposal'].browse(state['id'])
            if not proposal.name:
                return Respapi.error(errorDescription="Proposal does not exist or has been deleted.")

            # approve action
            proposal.action_approve()

            return Respapi.success({
                "id": proposal.id,
                "message": "Proposal approved"
            })
        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/proposal/reject'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def reject(self, **_):
        expected_schema = {'id': int, 'reason': str}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # proposal detail
            proposal = request.env['eps.proposal'].browse(state['id'])
            if not proposal.name:
                return Respapi.error(errorDescription="Proposal does not exist or has been deleted.")

            # mengikuti alur dashboard
            context = {
                'model_name': 'eps.proposal',
                'active_id': state['id'],
                'update_value': {
                    'approval_state': 'r',
                    'state': 'draft'
                }
            }

            request.env['eps.reject.approval'].create(
                {'reason': state['reason']}).eps_reject_approval(context)

            return Respapi.success({
                'id': proposal.id,
                'message': 'Proposal Rejected',
                'reason': state['reason']})

        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/proposal/cancel'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def cancel(self, **_):
        expected_schema = {'id': int, 'reason': str}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # proposal detail
            proposal = request.env['eps.proposal'].browse(state['id'])
            if not proposal.name:
                return Respapi.error(errorDescription="Proposal does not exist or has been deleted.")

            # mengikuti alur dashboard
            context = {
                'model_name': 'eps.proposal',
                'active_id': state['id'],
                'update_value': {
                    'approval_state': 'b',
                    'state': 'draft'
                }
            }
            request.env['eps.cancel.approval'].create(
                {'reason': state['reason']}).eps_cancel_approval(context)

            return Respapi.success({
                'id': proposal.id,
                'message': 'Proposal Canceled',
                'reason': state['reason']})

        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/proposal/<id>/message'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def thread(self, id=None, **params):
        try:
            # user
            user = request.env['res.users'].browse(request.session.uid)

            # proposal detail
            proposal = request.env['eps.proposal'].browse(int(id))
            # import ipdb; ipdb.set_trace()
            data = [{
                'id':message['id'],
                'user':{
                    "id":message['author_id'][0],
                    "name":message['author_id'][1],
                },
                'email_from':message['email_from'],
                'message_type':message['message_type'],

                'created_at':message['date'].strftime("%Y-%m-%d %H:%M:%S") if message['date'] else None,
                'record_name':message['record_name'],
                'body':message['body'] if message['body'] else None,
                'subtype':{
                    "id":message['subtype_id'][0],
                    "name":message['subtype_id'][1]
                },
                'tracking_value_ids':message['tracking_value_ids'],
                'is_discussion':message['is_discussion']

            } for message in proposal.message_ids.message_format() ]
            return Respapi.success(data)
        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/proposal/<id>/message/send'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def post(self, id=None, **params):
        expected_schema = {'body': str}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state
            
            # proposal detail
            proposal = request.env['eps.proposal'].browse(int(id))
            data= {
                'body':state['body'],
                'model':'eps.proposal',
                'res_id':proposal.id,
                'message_type':'comment',
                'subtype_id':1,
                'record_name':proposal.name
            }
            proposal.message_ids.create(data)

            return Respapi.success({"message": "Message send"})
            
        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))