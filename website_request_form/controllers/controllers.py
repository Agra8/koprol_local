import base64
import datetime
import json
import math
import os
import logging
import pytz
import requests
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers

from itertools import islice
from xml.etree import ElementTree as ET

import odoo

from odoo import http, models, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request, Response
from odoo.tools import OrderedSet
from odoo.addons.http_routing.models.ir_http import slug, slugify, _guess_mimetype
from odoo.addons.web.controllers.main import Binary
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.portal.controllers.web import Home
from datetime import date

_logger = logging.getLogger(__name__)
class WebsiteForm(Home):
    
    @http.route('/request_form', type='http', auth='public', website=True)
    def order(self, **kwargs):

        company = request.env['res.company'].sudo().search([])
        branch = request.env['res.branch'].sudo().search([])
        department = request.env['hr.department'].sudo().search([])
        job_title = request.env['hr.job'].sudo().search([])
        employee = request.env['hr.employee'].sudo().search([('job_id.name','like','%Manager%')])
        requestjrf = request.env['master.jrf.arf'].sudo().search([])
        return request.render("website_request_form.website_request_form", {
            'company': company,
            'branch': branch,
            'job': job_title,
            'department': department,
            'employee': employee,
            'requestjrf': requestjrf,
        })
    
    @http.route('/create_website_form/<string:model_name>', type='http', auth='public', methods=['POST'], website=True)
    def create_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search(
            [('model','=',model_name)]
        )
        if not model_record:
            return json.dumps(False)
        
        try:
            data = self.extract_data(model_record, request.params)
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})
        
        value = data['record']
        if not value.get('no_telp').isdigit() or len(value.get('no_telp')) < 11 or len(value.get('no_telp')) > 14:
            request._cr.rollback()
            return json.dumps({
                'error': _("Nomor Telp tidak sesuai format")
            }) 
            
        if 'Company' in value:
            value['company_id'] = int(value.get('Company'))
            del value['Company']

        if 'Branch' in value:
            value['branch_id'] = int(value.get('Branch'))
            del value['Branch']
        
        if 'Departement' in value:
            value['department_id'] = int(value.get('Departement'))
            del value['Departement']

        
        if 'job_title' in value:
            value['job_title'] = int(value.get('job_title'))
        
        if 'request_line_ids[]' in value:
            value['request_line_ids'] = value.get('request_line_ids[]')
            del value['request_line_ids[]']
        
        if 'requestform_id' in value:
            del value['requestform_id']
        
        if 'request_line_keterangan[]' in value:
            del value['request_line_keterangan[]']



        request_id = request.env[model_record.model].sudo().create(value)
        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = request_id.id
        return json.dumps({'id': request_id.id})
    
    def convert_list(self,values,type_var):
        ids = []
   
        for data in (values.split(',')):
            if type_var == 'form_id':
                dict_var = dict(form_id = int(data))
            if type_var == 'description':
                dict_var = dict(description = str(data))
            ids.append(dict_var)
             
        values = ids
        return values
            
    def extract_data(self,model,values):
        data = {
            'record': {},
            'attachments': [],
            'custom': '',
        }

        authorized_fields = model.sudo()._get_form_writable_fields()
        custom_fields = []

        for field_name, field_value in values.items():
            if hasattr(field_value, 'filename'):
                field_name = field_name.split('[',1)[0]

            else:
                try:
                    data['record'][field_name] = field_value
                except ValueError:
                    custom_fields.append((field_name, field_value))
                
        if 'request_line_ids[]' in data['record']:
            data['record']['request_line_ids[]'] = self.convert_list(data['record']['request_line_ids[]'], 'form_id') 
        if 'request_line_keterangan[]' in data['record']:
            data['record']['request_line_keterangan[]'] = self.convert_list(data['record']['request_line_keterangan[]'], 'description') 
            count_data = len(data['record']['request_line_ids[]'])
            i = 0
            while (i < count_data):
                data['record']['request_line_ids[]'][i]['keterangan'] = data['record']['request_line_keterangan[]'][i]['description']
                i = i + 1
        data['custom'] = "\n".join([u"%s: %s" % v for v in custom_fields])
        return data
    
    @http.route('/status_request', type='http', auth='public', website=True, csrf=False)
    def status_request(self, **kwargs):
        if kwargs:
            message = ''

            request_form = request.env['dms.request.form'].sudo().search([('name','=', kwargs['search'])])

            if not request_form:
                message += 'Maaf, nomor request tidak ditemukan mohon cek kembali nomor request Anda'

            return http.request.render('website_request_form.website_request_form_status', {
                'request_form': request_form,
                'message': message,
                'input': kwargs['search']
            }) 
        else:
            request.env['ir.rule'].clear_cache()
            return http.request.render('website_request_form.website_request_form')
    
    @http.route('/approval/<token_access>', type='http', auth='public', website=True)
    def verify_approval_request(self,token_access):
        today = date.today()
        get_token = token_access[5:]
        token_split = get_token.split("n")
        request_form = request.env['dms.request.form'].sudo().search([('id','=',int(token_split[0]))])
        if request_form:
            approval_line = request.env['dms.request.form.approval'].sudo().search([('request_form_id','=',request_form.id),('employee_id','=',int(token_split[1]))])
            if approval_line.state == 'approved' or approval_line.state == 'rejected':
                return http.request.render('website_request_form.sorry_page', {
                    'approval_line': approval_line
                })

            if approval_line:
                approval_line.write({
                'state': 'approved',
                'tanggal_approved': today
                })
                approval_open = request_form.approval_ids.search([
                    ('request_form_id', '=', request_form.id),
                    ('state', '=', 'open')
                ])
                if not approval_open:
                    request_form.write({
                        'state': 'approved'
                    })
            return http.request.render('website_request_form.website_request_form_approval', {
                'nama_transaksi': request_form.name,
                'nama_employee': approval_line.employee_id.name,
                'request_form': request_form
            })
        else:
            return http.request.render('website_request_form.not_found')
    
    @http.route('/reject/<token_access>', type='http', auth='public', website=True)
    def verify_reject_request(self,token_access):
        get_token = token_access[5:]
        token_split = get_token.split("n")
        request_form = request.env['dms.request.form'].sudo().search([('id','=',int(token_split[0]))])
        if request_form:
            approval_line = request.env['dms.request.form.approval'].sudo().search([('request_form_id','=',request_form.id),('employee_id','=',int(token_split[1]))])
            if approval_line.state == 'approved' or approval_line.state == 'rejected':
                return http.request.render('website_request_form.sorry_page', {
                    'approval_line': approval_line
                })
            return http.request.render('website_request_form.website_request_form_reject',{
                'request_form': request_form,
                'approval_line': approval_line,
            })
        else:
            return http.request.render('website_request_form.not_found')
    
    @http.route('/reject_request_form/<string:model_name>', type='http', auth='public', methods=['POST'], website=True)
    def reject_form(self,model_name, **kwargs):
        
        model_record = request.env['ir.model'].sudo().search(
            [('model', '=', model_name)]
        )
        today = date.today()
        if not model_record:
            return json.dumps(False)
        try:
            data = self.extract_data(model_record, request.params)
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})
        
        value = data['record']


        if 'request_form' in value:
            request_form = request.env['dms.request.form'].sudo().search([('id','=',int(value.get('request_form')))])
            line_id = int(value.get('approval_line'))
            alasan_reject = value.get('alasan_reject')
            approval_line = request.env[model_record.model].sudo().search([('id','=', line_id)])
            if approval_line:
                approval_line.write({
                'alasan_reject': alasan_reject,
                'state': 'rejected',
                'tanggal_reject': today
                })
                approval_open = request_form.approval_ids.search([
                    ('request_form_id', '=', request_form.id),
                    ('state', '=', 'open')
                ])
                if not approval_open:
                    request_form.write({
                        'state': 'rejected'
                    })
                    return json.dumps({'id': request_form.id})
                return json.dumps({'id': request_form.id})
