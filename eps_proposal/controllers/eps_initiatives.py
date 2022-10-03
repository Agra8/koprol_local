
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


class EpsInitiative(http.Controller):

    @http.route([f'{version}/initiatives'], type="http", auth="public", methods=['GET'], csrf=False)
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
            initiatives = request.env['eps.initiatives'].search(
                conditions, limit=limit, offset=offset, order=order)

            list = [{
                    'id': initiative.id,
                    'name': initiative.name,
                    'tanggal': initiative.date.strftime("%Y-%m-%d %H:%M:%S") if initiative.date is not False else None,
                    'reserved_amount': initiative.reserved_amount,
                    'company': {
                        'id': initiative.company_id.id,
                        'name': initiative.company_id.name,
                    } if initiative.company_id else None,
                    'branch': {
                        'id': initiative.branch_id.id,
                        'name': initiative.branch_id.name
                    } if initiative.branch_id else None,
                    'divisi': {
                        'id': initiative.divisi_id.id,
                        'name': initiative.divisi_id.name
                    } if initiative.divisi_id else None,
                    'department': {
                        'id': initiative.department_id.id,
                        'name': initiative.department_id.name
                    } if initiative.department_id else None,
                    } for initiative in initiatives]

            return Respapi.success(list)
        except MissKeyCheckerError as ae:
            _logger.exception("Validation: %s, %s" %
                              (str(request.httprequest.path), str(ae)))
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            return Respapi.error(errorDescription=str(me))
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/initiatives/<id>'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def detail(self, id=None, **params):
        try:
            # user
            # user = request.env['res.users'].browse(request.session.uid)

            # approval transaction
            approval = request.env['eps.approval.transaction'].browse(
                int(params['apvid'])) if "apvid" in params else False

            # initiative detail
            initiative = request.env['eps.initiatives'].browse(int(id))

            # initiatives lines
            initiative_lines = request.env['eps.initiatives.line'].search(
                [('initiatives_id', '=', int(id))])

            # quotation lines
            quotation_lines = request.env['eps.quotation'].sudo().search(
                [('initiatives_id', '=', int(id))])

            # approval lines initiative (id 509)
            approval_line = request.env['eps.approval.transaction'].search(
                [('transaction_id', '=', int(id)),('model_id','=',509)])

            canAction = approval.state in ["IN", "WA"] if approval else False
            detail = {
                'id': initiative.id,
                'name': initiative.name,
                'tanggal': initiative.date.strftime("%Y-%m-%d %H:%M:%S") if initiative.date is not False else None,
                'proposal': {
                    'id':initiative.proposal_id.id,
                    'name':initiative.proposal_id.name,
                },
                'proposal_amount': initiative.proposal_amount,
                'branch': {
                    'id': initiative.branch_id.sudo().id,
                    'name': initiative.branch_id.sudo().name,
                } if initiative.branch_id else None,
                'company': {
                    'id': initiative.company_id.id,
                    'name': initiative.company_id.name,
                } if initiative.company_id else None,
                'divisi': {
                    'id': initiative.divisi_id.id,
                    'name': initiative.divisi_id.name
                } if initiative.divisi_id else None,
                'department': {
                    'id': initiative.department_id.id,
                    'name': initiative.department_id.name
                } if initiative.department_id else None,
                'type': initiative.type,
                'category': initiative.proposal_line_id.categ_id.name,
                'reserved_amount': initiative.reserved_amount,
                'state': initiative.state,
                'pic': initiative.proposal_id.employee_id.name,
                'pic_contact': initiative.proposal_id.employee_id.mobile_phone if initiative.proposal_id.employee_id.mobile_phone else None,
                'po_number': initiative.purchase_order_list,
                'initiative_line': [
                    {
                        'id': initiative_line.id,
                        'branch': {
                            'id': initiative_line.branch_id.id,
                            'name': initiative_line.branch_id.name,
                        } if initiative_line.branch_id else None,
                        'supplier': {
                            'id': initiative_line.supplier_id.id,
                            'name': initiative_line.supplier_id.name,
                        } if initiative_line.supplier_id is not False else None,
                        'product': {
                            'id': initiative_line.product_id.id,
                            'name': initiative_line.product_id.product_tmpl_id.name,
                        },
                        'quantity': initiative_line.quantity,
                        'price_unit': initiative_line.price_unit,
                        'discount': initiative_line.discount,
                        'price_tax': initiative_line.price_tax,
                        'price_total': initiative_line.price_total,
                    } for initiative_line in initiative_lines
                ],
                'quotation_line': [
                    {
                        'id': quotation.id,
                        'name': quotation.name,
                        'supplier': {
                            'id': quotation.supplier_id.id,
                            'name': quotation.supplier_id.name
                        },
                        'reference': quotation.ref if quotation.ref else None,
                        'rev_no': quotation.revision,
                        'quotation_amount': quotation.quotation_amount,
                        'state': quotation.state,
                    } for quotation in quotation_lines
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

    @http.route([f'{version}/initiatives/approve'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def approve(self, **_):
        expected_schema = {'id': int}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # initiative detail
            initiative = request.env['eps.initiatives'].browse(state['id'])
            if not initiative.name:
                return Respapi.error(errorDescription="Proposal does not exist or has been deleted.")

            initiative.action_approve()

            return Respapi.success({"message": "Proposal approved"})
        except MissKeyCheckerError as ae:
            _logger.exception("Validation: %s, %s" %
                              (str(request.httprequest.path), str(ae)))
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/initiatives/reject'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def reject(self, **_):
        expected_schema = {'id': int, 'reason': str}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # initiative detail
            initiative = request.env['eps.initiatives'].browse(state['id'])
            if not initiative.name:
                return Respapi.error(errorDescription="Proposal does not exist or has been deleted.")

            # mengikuti alur dashboard
            context = {
                'model_name': 'eps.initiatives',
                'active_id': state['id'],
                'update_value': {
                    'approval_state': 'r',
                    'state': 'draft'
                }
            }
            request.env['eps.reject.approval'].create(
                {'reason': state['reason']}).eps_reject_approval(context)

            return Respapi.success({
                'message': 'Proposal Rejected',
                'reason': state['reason']})

        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/initiatives/cancel'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def cancel(self, **_):
        expected_schema = {'id': int, 'reason': str}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # initiative detail
            initiative = request.env['eps.initiatives'].browse(state['id'])
            if not initiative.name:
                return Respapi.error(errorDescription="Proposal does not exist or has been deleted.")

            # mengikuti alur dashboard
            context = {
                'model_name': 'eps.initiatives',
                'active_id': state['id'],
                'update_value': {
                    'approval_state': 'b',
                    'state': 'draft'
                }
            }
            request.env['eps.cancel.approval'].create(
                {'reason': state['reason']}).eps_cancel_approval(context)

            return Respapi.success({
                'message': 'Proposal Canceled',
                'reason': state['reason']})

        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/initiatives/<id>/message'], type="http", auth="public", methods=['GET'], csrf=False)
    @auth.check_token
    def thread(self, id=None, **params):
        try:
            # user
            user = request.env['res.users'].browse(request.session.uid)

            # initiative detail
            initiative = request.env['eps.initiatives'].browse(int(id))
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

            } for message in initiative.message_ids.message_format() ]
            return Respapi.success(data)
        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    @http.route([f'{version}/initiatives/<id>/message/send'], type="json", auth="public", methods=['POST'], csrf=False)
    @auth.check_token
    def post(self, id=None, **params):
        expected_schema = {'body': str}
        try:
            state = request.jsonrequest
            checker = Checker(expected_schema)
            result = checker.validate(state)
            assert result == state

            # initiative detail
            initiative = request.env['eps.initiatives'].browse(int(id))
            data= {
                'body':state['body'],
                'model':'eps.initiatives',
                'res_id':initiative.id,
                'message_type':'comment',
                'subtype_id':1,
                'record_name':initiative.name
            }
            initiative.message_ids.create(data)
    
            return Respapi.success({"message": "Message send"})
            
        except MissKeyCheckerError as ae:
            return Respapi.error(error=str(ae.args[0]['code']) if 'code' in ae.args[0] else "Error", errorDescription=str(ae.args[0]['message']) if 'message' in ae.args[0] else ae)
        except MissingError as me:
            err = str(me).split('\n')
            return Respapi.error(errorDescription=err[0])
        except Exception as e:
            return Respapi.error(errorDescription=str(e))

    # def remove_html_tags(text):
    #     """Remove html tags from a string"""
    #     import re
    #     clean = re.compile('<.*?>')
    #     return re.sub(clean, '', text)