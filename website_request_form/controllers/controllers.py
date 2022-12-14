import base64
import datetime
import json
import math
import os
import logging
import pytz
import requests
from werkzeug.datastructures import Headers
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers
import cryptocode

from itertools import islice
from xml.etree import ElementTree as ET
from cryptography.fernet import Fernet

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
    def load_key(self):
        return open("secret.key", "rb").read()

    @http.route('/request_form', type='http', auth='public', website=True)
    def order(self, **kwargs):

        company = request.env['res.company'].sudo().search([])
        branch = request.env['res.branch'].sudo().search([])
        department = request.env['hr.department'].sudo().search([])
        job_title = request.env['hr.job'].sudo().search([])
        employee = request.env['hr.employee'].sudo().search(
            [('job_id.name', 'like', '%Manager%')])
        requestjrf = request.env['eps.master.jrf.arf'].sudo().search([])
        tipe_sistem = request.env['eps.sistem.master'].sudo().search([], order='sequence asc')
        return request.render("website_request_form.website_request_form", {
            'company': company,
            'branch': branch,
            'job': job_title,
            'department': department,
            'employee': employee,
            'requestjrf': requestjrf,
            'tipe_sistem': tipe_sistem,
        })

    @http.route('/create_website_form/<string:model_name>', type='http', auth='public', methods=['POST'], website=True)
    def create_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search(
            [('model', '=', model_name)]
        )

        model_record_attachment = request.env['ir.model'].sudo().search(
            [('model', '=', 'eps.request.form.line')]
        )

        if not model_record:
            return json.dumps(False)
        try:
            data = self.extract_data(model_record, request.params)
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})

        extension = {0: ['drawio', 'pdf', 'xls', 'xlsx',
                         'doc', 'docx', 'zip', 'rar', 'jpg', 'png', 'jpeg']}
        max_size = {0: 100000000}
        file_name = {0: 'Lampiran'}

        value = data['record']

        if 'nik' in value:
            value['nik'] = str(value.get('nik'))

        # if not value.get('no_telp').isdigit() or len(value.get('no_telp')) < 11 or len(value.get('no_telp')) > 14:
        #     request._cr.rollback()
        #     return json.dumps({
        #         'error': _("Nomor Telp tidak sesuai format")
        #     })

        if 'company_id' in value:
            value['company_id'] = int(value.get('company_id'))

        if 'branch_id' in value:
            value['branch_id'] = int(value.get('branch_id'))

        if 'department_id' in value:
            value['department_id'] = int(value.get('department_id'))

        if 'job_title' in value:
            value['job_title'] = int(value.get('job_title'))

        if 'requestform_id' in value:
            del value['requestform_id']

        if 'request_line_keterangan[]' in value:
            del value['request_line_keterangan[]']

        if 'request_sistem_ids' in value:
            del value['request_sistem_ids']
        
        try:
            request_id = request.env[model_record.model].sudo().create(value)
        except Exception as err:
            _logger.error(err)
            return False, f'Error saat create Ticket: {err}, \
                mohon cek data - data'
        if data['attachments']:
            attachment = data['attachments']
            id_record = [
                id_record.id for id_record in request_id.request_line_ids]
            attachment_status, result = self.insert_attachment(
                model_record,
                request_id.id,
                id_record,
                attachment,
                extension,
                max_size,
                file_name
            )
            if not attachment_status:
                request._cr.rollback()
                return json.dumps({
                    'error': _(result)
                })
        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = request_id.id
        return json.dumps({'id': request_id.id})

    def convert_list(self, values, type_var):
        ids = []

        for data in (values.split(',')):
            if type_var == 'form_id':
                data_id = data.split('-')
                dict_var = dict(form_id=int(data_id[0]))
            if type_var == 'description':
                dict_var = dict(description=str(data))
            if type_var == 'sistem_id':
                dict_var = dict(sistem_id=0 if data == 'NULL' else int(data))
            ids.append(dict_var)
        values = ids
        return values

    def extract_data(self, model, values):
        data = {
            'record': {},
            'attachments': [],
            'custom': '',
        }

        authorized_fields = model.sudo()._get_form_writable_fields()
        custom_fields = []
        request_line_ids = []
        for field_name, field_value in values.items():
            if hasattr(field_value, 'filename'):
                field_name = field_name.split('[', 1)[0]
                if not (field_name in authorized_fields and authorized_fields[field_name]['type'] == 'binary'):
                    field_value.field_name = field_name
                    data['attachments'].append(field_value)
            else:
                try:
                    data['record'][field_name] = field_value
                except ValueError:
                    custom_fields.append((field_name, field_value))

        if 'request_line_ids' in data['record']:

            if 'request_sistem_ids' in data['record']:
                data['record']['request_sistem_ids'] = self.convert_list(
                    data['record']['request_sistem_ids'], 'sistem_id')
            data['record']['request_line_ids'] = self.convert_list(
                data['record']['request_line_ids'], 'form_id')
            data['record']['request_line_keterangan[]'] = self.convert_list(
                data['record']['request_line_keterangan[]'], 'description')
            for idx, datas in enumerate(data['record']['request_line_ids']):
                tipe_request_obj = request.env['eps.master.jrf.arf'].sudo().browse(
                    datas['form_id'])
                request_line_ids.append([0, 0, {
                    'request_id': datas['form_id'],
                    'keterangan': data['record']['request_line_keterangan[]'][idx]['description'],
                    'sistem_id': data['record']['request_sistem_ids'][idx]['sistem_id'] if 'request_sistem_ids' in data['record'] else '',
                    'value_approval': tipe_request_obj.approval_default,
                    'teams_id': tipe_request_obj.teams_id.id
                }])
            data['record']['request_line_ids'] = request_line_ids

        data['custom'] = "\n".join([u"%s: %s" % v for v in custom_fields])
        return data

    def insert_attachment(self, model, id_header, id_record, files, extension, max_size, file_name):
        attachment = False

        attachment_value = []
        model_name = model.sudo().model
        record = model.env[model_name].browse(id_header)
        list_ext = [ext for ext in extension[0]]
        list_size = [size for size in max_size.values()]
        list_name = [name for name in file_name.values()]
        list_id_record = [id_record for id_record in id_record]

        for file_, id_record in zip(files,  list_id_record):
            value = file_.read()
            file_length = file_.tell()
            uploaded_name = file_.filename.split('-')
            uploaded_ext = uploaded_name[-1].split('.')
            valid_filename = f'{list_name[0]} - {record.name.replace(" ","_")}.{uploaded_ext[-1]}'

            if list_name[0] != uploaded_name[0] or \
                    record.name.replace(' ', '_') != uploaded_ext[0]:
                file_.filename = valid_filename

            if uploaded_ext[-1] not in list_ext:
                return False, f"file {list_name[0]} seharusnya ber-ekstensi {list_ext} !"

            if file_length > list_size[0]:
                return False, f"ukuran file ({file_length}) melebehi batas!"

            attachment = request.env['eps.request.form.line'].sudo().search([
                ('id', '=', id_record)
            ], limit=1)
            if attachment:
                try:
                    attachment.sudo().write({
                        'filename': file_.filename,
                        'file_upload': base64.encodebytes(value),
                        'type_file': uploaded_ext[1],
                    })
                except Exception as err:
                    _logger.error(err)
                    return False, f'Error upload file {file_.filename}, \
                        mohon cek ukuran file beserta formatnya !'

            else:
                attachment_value.append({
                    'filename': file_.filename,
                    'file_upload': base64.encodebytes(value),
                    'type_file': uploaded_ext[1],
                })

        if attachment_value:
            try:
                attachment_id = request.env['eps.request.form.line'].sudo().create(
                    attachment_value)
                return True, attachment_id

            except Exception as err:
                _logger.error(err)
                return False, 'Error saat upload attachment, \
                    mohon cek ukuran file beserta formatnya !'
        elif attachment:
            return True, 'Attachment is updated'

    @http.route('/status_request', type='http', auth='public', website=True, csrf=False)
    def status_request(self, **kwargs):
        if kwargs:
            message = ''
            search = str(kwargs['search']).split("/")
            if search[0] == 'RF':
                request_form = request.env['eps.request.form'].sudo().search(
                    [('name', '=', kwargs['search'])])
            elif search[0] == 'RFL':
                request_form = request.env['eps.request.form.line'].sudo().search(
                    [('name', '=', kwargs['search'])])

            if not request_form:
                message += 'Maaf, nomor request tidak ditemukan mohon cek kembali nomor request Anda'

            return http.request.render('website_request_form.website_request_form_status', {
                'request_form': request_form,
                'search': search[0],
                'message': message,
                'input': kwargs['search']
            })
        else:
            request.env['ir.rule'].clear_cache()
            return http.request.render('website_request_form.website_request_form')

    @http.route('/approval/<token_access>', type='http', auth='public', website=True)
    def verify_approval_request(self, token_access):
        key = self.load_key()
        f = Fernet(key)
        decrypt_token = f.decrypt(bytes(token_access, encoding='utf8'))
        get_token = decrypt_token[5:]
        get_token = get_token.decode("utf-8")
        token_split = str(get_token).split("n")
        request_form = request.env['eps.request.form.line'].sudo().search(
            [('id', '=', int(token_split[0]))])
        if request_form:
            approval_line = request.env['eps.request.form.approval'].sudo().search(
                [('request_form_line_id', '=', request_form.id), ('employee_id', '=', int(token_split[1]))])
            if approval_line.state == 'approved' or approval_line.state == 'rejected':
                return http.request.render('website_request_form.sorry_page', {
                    'approval_line': approval_line
                })

            if approval_line:
                # approval_line.write({
                # 'state': 'approved',
                # 'tanggal_approved': today
                # })
                # approval_open = request_form.additional_approval_ids.search([
                #     ('request_form_line_id', '=', request_form.id),
                #     ('state', '=', 'open')
                # ])
                # if not approval_open:
                #     request_form.write({
                #         'state': 'approved'
                #     })
                request_form.action_approve()
            return http.request.render('website_request_form.website_request_form_approval', {
                'nama_transaksi': request_form.request_form_id.name,
                'nama_employee': approval_line.employee_id.name,
                'request_form': request_form
            })
        else:
            return http.request.render('website_request_form.not_found')

    @http.route('/reject/<token_access>', type='http', auth='public', website=True)
    def verify_reject_request(self, token_access):
        key = self.load_key()
        f = Fernet(key)
        decrypt_token = f.decrypt(bytes(token_access, encoding='utf8'))
        get_token = decrypt_token[5:]
        get_token = get_token.decode("utf-8")
        token_split = get_token.split("n")
        request_form = request.env['eps.request.form.line'].sudo().search(
            [('id', '=', int(token_split[0]))])
        if request_form:
            approval_line = request.env['eps.request.form.approval'].sudo().search(
                [('request_form_line_id', '=', request_form.id), ('employee_id', '=', int(token_split[1]))])
            if approval_line.state == 'approved' or approval_line.state == 'rejected':
                return http.request.render('website_request_form.sorry_page', {
                    'approval_line': approval_line
                })
            return http.request.render('website_request_form.website_request_form_reject', {
                'request_form': request_form,
                'approval_line': approval_line,
            })
        else:
            return http.request.render('website_request_form.not_found')

    @http.route('/reject_request_form/<string:model_name>', type='http', auth='public', methods=['POST'], website=True)
    def reject_form(self, model_name, **kwargs):

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
            request_form = request.env['eps.request.form.line'].sudo().search(
                [('id', '=', int(value.get('request_form')))])
            line_id = int(value.get('approval_line'))
            alasan_reject = value.get('alasan_reject')
            approval_line = request.env[model_record.model].sudo().search([
                ('id', '=', line_id)])
            if approval_line:
                approval_line.write({
                    'alasan_reject': alasan_reject,
                    'state': 'rejected',
                    'tanggal_reject': today
                })
                approval_open = request_form.approval_ids.search([
                    ('request_form_line_id', '=', request_form.id),
                    ('state', '=', 'open')
                ])
                if not approval_open:
                    request_form.write({
                        'state': 'rejected'
                    })
                    return json.dumps({'id': request_form.id})
                return json.dumps({'id': request_form.id})

    # RUN Manifest and Service Worker for PWA Feature (SOON)

    @http.route("/manifest.json", type="http", auth="public")
    def web_app_manifest(self):
        manifest_data = request.env['res.config.settings'].sudo(
        )._get_pwa_manifest_data()
        return request.make_response(
            json.dumps(
                {
                    "name": manifest_data['name'],
                    "short_name": manifest_data['short_name'],
                    "theme_color": manifest_data['theme_color'],
                    "background_color": manifest_data['background_color'],
                    "display": manifest_data['display'],
                    "orientation": manifest_data['orientation'],
                    "scope": "/",
                    "start_url": "/",
                    "icons": manifest_data['icons']
                }
            ),
            headers=[("Content-Type", "application/json;charset=utf-8")],
        )

    @http.route("/service_worker.js", type="http", auth="public")
    def render_service_worker(self):
        js_code = """
            const aktiv_CACHE = "Request-form-cache"
            const assets = [
                "/",
            ]

            self.addEventListener("install", installEvent => {
                installEvent.waitUntil (
                    caches.open(aktiv_CACHE).then(cache => {
                        cache.addAll(assets)
                    })
                )
            });

            self.addEventListener("fetch", fetchEvent => {
                fetchEvent.respondWith(
                    caches.match(fetchEvent.request).then(res => {
                        return res || fetch(fetchEvent.request)
                    })
                )
            });
        """

        return request.make_response(
            js_code,
            [('Content-Type', "text/javascript; charset=utf-8"),
             ('Content-Length', len(js_code))]
        )

    @http.route("/web/service_worker.js", type="http", auth="public")
    def render_service_worker_backend(self):
        js_code = """
            const aktiv_CACHE = "Backend-Cache"
            const assets = [
                "/",
            ]

            self.addEventListener("install", installEvent => {
                installEvent.waitUntil (
                    caches.open(aktiv_CACHE).then(cache => {
                        cache.addAll(assets)
                    })
                )
            });

            self.addEventListener("fetch", fetchEvent => {
                fetchEvent.respondWith(
                    caches.match(fetchEvent.request).then(res => {
                        return res || fetch(fetchEvent.request)
                    })
                )
            });
        """

        return request.make_response(
            js_code,
            [('Content-Type', "text/javascript; charset=utf-8"),
             ('Content-Length', len(js_code))]
        )

    @http.route('/get_profile', methods=['POST'],type='json', auth='public', website=True, csrf=False)
    def get_profile(self, **post):
        post = request.jsonrequest
        # import ipdb; ipdb.set_trace()
        if not post.get('nik'):
            return 400,'Harus ada NIK(Nomor Induk Karyawan) !'

        nik = post.get('nik')
        employee_obj = request.env['hr.employee'].suspend_security().search([('nip','=',nik)],limit=1)
        if not employee_obj:
            return 400,'NIK (%s) belum terdaftar di sistem, silahkan isi manual form dibawah' %(post.get('nik'))
        name = employee_obj.name
        nik = employee_obj.nip
        company_id = employee_obj.company_id.id or None
        branch_id = employee_obj.branch_id.id or None
        department_id = employee_obj.department_id.id or None
        email = employee_obj.work_email or None
        job_id = employee_obj.job_id.id or None

        data_employee = {
            'name': name,
            'nik': nik,
            'company_id': company_id,
            'branch_id': branch_id,
            'department_id': department_id,
            'email': email,
            'job_id': job_id
        }
        return 200, data_employee
