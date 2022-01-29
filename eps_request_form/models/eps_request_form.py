#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from email import header
import string, random, cryptocode, os
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode
from lxml import etree

# 3:  imports of odoo
from typing import Sequence
from odoo import models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

# 4:  imports from odoo modules
from odoo.exceptions import Warning

# 5: local imports

# 6: Import of unknown third party lib

class RequestForm(models.Model):
    _name="eps.request.form"
    _description="Request Form for JRF / ARF"

    # 7: defaults methods
    
    def _get_default_date(self):
        return (datetime.now() + relativedelta(hours=7)).date()
    

    # 8: fields
    name = fields.Char(string='Name', index=True)
    date = fields.Date(string='Date', readonly=True,default=_get_default_date)
    is_maindealer = fields.Boolean(string='Main Dealer')
    alasan_reject = fields.Text(string='Alasan Reject')
    total_approval = fields.Float(string='Approval Percentage')
    name_pegawai = fields.Char(string='Nama Pegawai')
    no_telp = fields.Char(string="Nomor Telp")
    state = fields.Selection(string='State', selection=[('draft','Draft'),('rfa', 'Waiting for Approval'), ('cancel', 'Cancel'),('open', 'Open'), ('done', 'Done')], default='draft')
    # Audit Trail
    request_uid = fields.Many2one(comodel_name='res.users',string='Requested by')
    request_date = fields.Datetime(string='Requested on')
    reject_uid = fields.Many2one(comodel_name='res.users',string='Rejected by')
    reject_date = fields.Datetime(string='Rejected on')
    confirm_uid = fields.Many2one(comodel_name='res.users',string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')
    done_uid = fields.Many2one(comodel_name='res.users', string='Done by')
    done_date = fields.Datetime(string='Done on')

    # 8: Relational Fields
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    branch_id = fields.Many2one(comodel_name='res.branch', string='Branch')
    divisi_id = fields.Many2one(comodel_name='eps.divisi', string='Divisi')
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')
    employee_id = fields.Many2one(comodel_name='hr.employee',string='Employee')
    request_line_ids = fields.One2many(comodel_name='eps.request.form.line',inverse_name='request_form_id', string='Request')
    job_title = fields.Many2one(comodel_name='hr.job',string='Job Title')


    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.branch'].suspend_security().browse(vals['branch_id'])
            doc_code = branch_obj.code
            vals['name'] = self.env['ir.sequence'].suspend_security().get_per_doc_code(doc_code,'RF')
            vals['divisi_id'] = self.env['eps.divisi'].suspend_security().search([('name', '=', 'Umum')]).id
            create = super(RequestForm, self).create(vals)
        return create
    
    def unlink(self):
        raise Warning('Request Form tidak bisa di delete !')
    
    def copy(self):
        raise Warning('Perhatian!\nData tidak bisa diduplikasi.')


    def action_rfa(self):    
        for request in self.request_line_ids:
            if request.additional_approval_ids:
                template = request.env.ref('eps_request_form.template_mail_request_form_result')
                mail = request.env['mail.template'].suspend_security().browse(template.id)
                for user in request.additional_approval_ids.employee_id:
                    request.email_penerima = user.work_email
                    request.penerima = user.name
                    request.token_penerima = request.create_token(request.id, user.id)
                    path = "/approval/%s" % request.token_penerima
                    path_reject = "/reject/%s" % request.token_penerima
                    request.approval_url = request.get_url() + path
                    request.reject_url = request.get_url() + path_reject
                    mail.send_mail(request.id, force_send=True)
            if int(request.value_approval) > 0:
                request.env['eps.matrix.approval.line'].request_by_value(request, int(request.value_approval), send_email=False)
        self.write({
            'state': 'rfa',
            'request_uid':self.env.user.id,
            'request_date':self._get_default_date()
        })
    
    def action_open(self):
        self.write({
            'state': 'open'
        })

    def action_done(self):
        self.write({
            'state': 'closed',
            'done_uid': self.env.user.id,
            'done_date': self._get_default_date()
        })

    
    def action_request(self):
        self.ensure_one()
        form_id = self.env.ref('eps_request_form.eps_request_form_line_form_wizard').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Form Line',
            'view_id': False,
            'views': [(form_id,'form')],
            'view_mode': 'form',
            'res_model': 'eps.request.form.line.wizard',
            'target': 'new',
            'view_type': 'form',
            'context': {
                'active_id': self.id,
                'company_id': self.company_id.id,
                'branch_id': self.branch_id.id
            }
        }
   
    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def _change_group_by_level(self,vals):
        
        name_job_level = False
        if vals == '1':
            name_job_level = 'CLERK'
        elif vals == '2':
            name_job_level= 'STAFF'
        elif vals == '3':
            name_job_level = 'SUPERVISOR'
        elif vals == '4':
            name_job_level = 'MANAGER'
        elif vals == '5':
            name_job_level = 'OM/GM/SM'
        elif vals == '6':
            name_job_level = 'CHIEF/VICE PRECIDENT'
        group_obj = self.env['res.groups'].suspend_security().search([('name','=', name_job_level)])
        if group_obj:
            if name_job_level == 'CLERK':
                vals = group_obj.id
            elif name_job_level == 'STAFF':
                vals = group_obj.id
            elif name_job_level == 'SUPERVISOR':
                vals = group_obj.id
            elif name_job_level == 'MANAGER':
                vals = group_obj.id
            elif name_job_level == 'OM/GM/SM':
                vals = group_obj.id
            elif name_job_level == 'CHIEF/VICE PRECIDENT':
                vals = group_obj.id
            name_job_level = False
        return vals
    
    def eps_request_form_view(self):
        name= 'Request Form'
        tree_id = self.env.ref('eps_request_form.eps_request_form_view_tree').id
        form_id = self.env.ref('eps_request_form.eps_request_form_view_form').id
        search_id = self.env.ref('eps_request_form.eps_request_form_search').id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'eps.request.form',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'search_default_state_draft': 1,
                'search_default_group_company': 1,
                'readonly_by_pass': 1
            }
        }
     
class RequestFormLine(models.Model):
    _name="eps.request.form.line"
    _inherit = ['mail.thread']
    _description="Request Form Line"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    @api.depends('filename_upload')
    def compute_filename(self):
        for record in self:
            if record.filename_upload:
                try:
                    image_lampiran = self.env['eps.config.files'].suspend_security().get_img(record.filename_upload)
                    record.file_show = image_lampiran
                    if record.type_file == 'pdf':
                        record.file_pdf = image_lampiran
                        record.file_image = False
                    elif record.type_file == 'jpg' or record.type_file == 'jpeg' or record.type_file == 'png' :
                        record.file_image = image_lampiran
                        record.file_pdf = False
                    else:
                        record.file_image = False
                        record.file_pdf = False
                except FileNotFoundError as err:
                    _logger.error(err)
                    record.file_show = False
                    record.file_image = False
                    record.file_pdf = False
            else:
                record.file_show = False
                record.file_image = False
                record.file_pdf = False
    
    @api.model
    def _expand_groups(self, states, domain, order):
        return ['draft', 'approved', 'rejected', 'open', 'done']
    
    def _key_gen(self):
        key_len = 5
        random_letters = string.ascii_letters+string.digits
        keylist = [random.choice(random_letters) for i in range (key_len)]
        return ("".join(keylist))

    
    # 8: fields

    name=fields.Char(string='Name')
    date=fields.Date(string='Date', default=_get_default_date)
    keterangan = fields.Text(string='Keterangan')
    state = fields.Selection(string='State',  selection=[('draft','Draft'),('approved','Approved'),('rejected','Rejected'),('open', 'Open'),('done', 'Done')], default='draft', group_expand='_expand_groups')
    value_approval = fields.Selection(string='Default Approval',
    selection=[
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
        ])
    
    file_upload = fields.Binary(string='Upload Lampiran')
    filename_upload = fields.Char(string='Nama Lampiran Upload')
    filename = fields.Char(string='Nama Lampiran')
    file_show = fields.Binary(string='lampiran_show', compute='compute_filename')
    file_download = fields.Binary(string='Download Lampiran', related='file_show')
    file_pdf = fields.Binary(string='file pdf', compute='compute_filename')
    file_image = fields.Binary(string='File Image', compute='compute_filename')
    type_file = fields.Char(string='Tipe File', default='NULL')
    user_request = fields.Char(String='User Request', related='request_form_id.name_pegawai')
    reason = fields.Char(string='Alasan Reject')
    email_penerima = fields.Char()
    penerima = fields.Char()
    token_penerima = fields.Char()
    approval_url = fields.Char()
    reject_url = fields.Char()
    request_state = fields.Selection(related="request_form_id.state")

    # Audit trail
    request_uid = fields.Many2one(comodel_name='res.users',string='Requested by',related="request_form_id.request_uid")
    request_date = fields.Datetime(string='Requested on',related="request_form_id.request_date")
    reject_uid = fields.Many2one(comodel_name='res.users',string='Rejected by')
    reject_date = fields.Datetime(string='Rejected on')
    approve_uid = fields.Many2one(comodel_name='res.users',string='Approve by')
    approve_date = fields.Datetime(string='Approve on')
    done_uid = fields.Many2one(comodel_name='res.users', string='Done by')
    done_date = fields.Datetime(string='Done on')
    
    # 9: Relations Fields
    request_form_id = fields.Many2one(comodel_name='eps.request.form', string='Request Form')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', related='request_form_id.company_id', store=False)
    branch_id = fields.Many2one(comodel_name='res.branch', string='Branch', related='request_form_id.branch_id', store=False)
    divisi_id = fields.Many2one(comodel_name='eps.divisi', string='Divisi', related='request_form_id.divisi_id', store=False)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department', related='request_form_id.department_id', store=False)
    request_id = fields.Many2one(comodel_name='eps.master.jrf.arf', string='Master Request')
    employee_id = fields.Many2one(comodel_name='hr.employee',string='PIC')
    sistem_id = fields.Many2one(comodel_name='eps.sistem.master', string='Master Sistem')
    approval_ids = fields.One2many(comodel_name='eps.approval.transaction', inverse_name='transaction_id', string='Approval', copy=False)
    additional_approval_ids = fields.One2many(comodel_name='eps.request.form.approval',inverse_name='request_form_line_id', string='Additional Approval JRF/ARF')
    
    @api.model
    def create(self, vals: dict):
        branch_obj = self.env['eps.request.form'].suspend_security().browse(vals['request_form_id']).branch_id
        doc_code = branch_obj.code
        vals['name'] = self.env['ir.sequence'].suspend_security().get_per_doc_code(doc_code,'RFL')
        if vals.get('type_file'):
            type_file = vals.get('type_file')
        
        file_upload = False
        if vals.get('file_upload'):
            file_upload = vals['file_upload']
            vals['file_upload'] = False   
        ids = super(RequestFormLine, self).create(vals)
     
        if file_upload:
            tmp_lampiran = vals['filename'].split('.')
            filename_up = f'[{ids.id}]{tmp_lampiran[0]}-{str(vals["request_line_id"])}-request_form.{tmp_lampiran[len(tmp_lampiran) - 1]}'
            self.env['eps.config.files'].suspend_security().upload_file(filename_up, file_upload)
            ids.filename_upload = filename_up

        #  ids.approval_ids.write({'user_id': employee_id.user_id.id})
        return ids

    def write(self, vals: dict):
        if vals.get('value_approval'):
            aprv_transcation_obj = self.env['eps.approval.transaction'].search([('transaction_id', '=', self.id)])
            aprv_transcation_obj.write({
                'value': vals['value_approval'],
            })
        if vals.get('type_file'):
            type_file = vals.get('type_file')
        if vals.get('value_approval', False):
            if vals.get('value_approval') != self.value_approval:
                self._message_log(body=_('<b>Value Approval Changed ! </b> From %d to %d') % (self.value_approval, int(vals.get('value_approval'))))
        if vals.get('employee_id', False):
            if vals.get('employee_id') != self.employee_id:
                employee_obj = self.env['hr.employee'].suspend_security().browse(vals.get('employee_id'))
                self._message_log(body=_('<b>PIC Changed!</b> From %s to %s') % (self.employee_id.name,employee_obj.name))
        if vals.get('state', False):
            if not self.employee_id:
                raise Warning('PIC belum ditambahkan ! \n silahkan lakukan assign terlebih dahulu')
            if vals.get('state') != self.state:
                self._message_log(body=_('<b>State Changed!</b> From %s to %s') % (self.state, str(vals.get('state'))))
            
        if vals.get('file_upload'):
            file_upload = vals['file_upload']
            vals['file_upload'] = False
            tmp_lampiran = vals['filename'].split('.')
            filename_up = f'[{self.id}]{tmp_lampiran[0]}-request_form.{tmp_lampiran[len(tmp_lampiran) - 1]}'
            filename_up = filename_up.replace('/', '-')
            self.env['eps.config.files'].suspend_security().upload_file(filename_up, file_upload)
            vals['filename_upload'] = filename_up
        return super(RequestFormLine, self).write(vals)
    
   
    
    def action_approve(self):
        if self.additional_approval_ids:
            self.action_additional_approve()
        if self.approval_ids:
            self.env['eps.matrix.approval.line'].approve(self)
            approval_matrix_open = self.env['eps.approval.transaction'].search([
                ('transaction_id', '=', self.id),
                ('state', '=', 'IN')
            ])

            if not approval_matrix_open:
                self.write({
                    'state': 'approved'
                })
        header_open = self.env['eps.request.form.line'].search(
            [
                ('request_form_id', '=', self.request_form_id.id),
                ('state', '=', 'draft')
            ]
        )
        if not header_open:
            self.request_form_id.write({
                'state': 'open'
            })
        

    def action_additional_approve(self):
        approval = self._check_user_groups()
        if not approval.employee_id:
            approval.write({
                'employee_id': self.env.user.employee_id,
                'user_id': self.env.user.id,
                'state': 'approved',
                'tanggal_approved': self._get_default_date()
            })
 
        approval.write({
            'state': 'approved',
            'tanggal_approved': self._get_default_date()
            })
       
        approval_open = self.additional_approval_ids.search([
            ('request_form_line_id', '=', self.id),
            ('state', '=', 'open')
        ])
        if not approval_open:
            self.write({
                'state': 'approved'
            })
    
    def action_reject_form(self):
        line_obj = self.env['eps.request.form.line'].browse(self._context['res_id'])
        self.env['eps.matrix.approval.line'].reject(line_obj, self.reason)
        line_obj.write({
            'state': 'rejected'
        })
    
    def action_done(self):
        self.write({
            'state': 'done'
        })
    
    
    def action_reject(self):
        form_id = self.env.ref('eps_request_form.eps_request_form_line_reject_form').id
        return {
            'name': ('Alasan Reject'),
            'res_model': 'eps.request.form.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'view_type': 'form',
            'context': {
                'res_id': self.id,
            }
        }
    
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        url_params = {
            'id': self.id,
            'view_type': 'form',
            'model': self._name,
        }
        params = '/web?#%s' % url_encode(url_params)
        return base_url + params
            
    def get_url(self):
        urls = request.httprequest.url.replace('//','/').split('/')
        base_url = urls[0] + "//" + urls[1]
        return base_url
    
    def generate_key(self):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    
    def load_key(self):
         file_exist = os.path.exists('./secret.key')
         if file_exist:
            return open("secret.key", "rb").read()
         else:
            return False

    def create_token(self, id_request_form, id_penerima):
        if not self.load_key():
            self.generate_key()
        token = self._key_gen()+str(id_request_form)+'n'+str(id_penerima)
        key = self.load_key()
        f = Fernet(key)
        token_encoded = f.encrypt(bytes(token,encoding='utf8'))
        return token_encoded

    def action_assign(self):
        form_id = self.env.ref('eps_request_form.eps_request_form_line_assign_form').id
        employee_ids = []
        if self.request_id.teams_id:
            form_id = self.env.ref('eps_request_form.eps_request_form_line_domain_assign_form').id
            employee_ids = [employee.employee_id.id for employee in self.request_id.teams_id.teams_line_ids]
        return {
            'name': ('Assign'),
            'res_model': 'eps.request.form.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'view_type': 'form',
            'context': {
                'domain_employee_ids': employee_ids,
                'res_id': self.id,
                'default_employee_id': False,
            }
        }
    
    def action_save_pic(self):
        line_obj = self.env['eps.request.form.line'].browse(self._context['res_id'])
        line_obj.write({
            'employee_id': self.employee_id,
            'state': 'open'
        })
    
       
    def _check_user_groups(self):
        approval_obj = self.additional_approval_ids.search([
            ('request_form_line_id', '=', self.id),
            ('state','=','open')
        ])

        for approval in approval_obj:
            # TODO: create check if user already approving with this request
            user_approval_obj = self.additional_approval_ids.search([
                ('request_form_line_id', '=', self.id),
                ('user_id','=', self.env.user.id),
                ('state', '=','approved')
            ])
            if self.env.user.has_group(approval.group_id.get_xml_id().popitem()[1]) and not user_approval_obj:
                return approval
        
        raise Warning("Anda 'Tidak Dapat' atau 'Sudah' melakukan Approval. \nPeriksa Tab Approval.")
    
    def eps_request_form_line_view(self):
        name= 'Request Form Line'
        tree_id = self.env.ref('eps_request_form.eps_request_form_line_view_tree').id
        form_id = self.env.ref('eps_request_form.eps_request_form_line_view_form').id
        kanban_id = self.env.ref('eps_request_form.eps_request_form_line_kanban_view').id
        search_id = self.env.ref('eps_request_form.eps_request_form_line_search').id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'eps.request.form.line',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'views': [(kanban_id, 'kanban'),(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'search_default_group_company': 1,
                'readonly_by_pass': 1
            }
    }

class RequestFormLineWizard(models.TransientModel):
    _name="eps.request.form.line.wizard"
    _description="Request Form Line Wizard"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    # 8: fields

    name=fields.Char(string='Name')
    date=fields.Date(string='Date', default=_get_default_date)
    keterangan = fields.Text(string='Keterangan')
    tipe_form = fields.Char(string='Sistem', related='request_id.type_form_id.name')

    # 9: Relations Fields
    request_id = fields.Many2one(comodel_name='eps.master.jrf.arf', string='Master Request')
    sistem_id = fields.Many2one(comodel_name='eps.sistem.master', string='Sistem')
    approval_ids = fields.One2many(comodel_name='eps.approval.transaction', inverse_name='transaction_id', string='Approval', domain=[('model_id','=','eps.request.form')], copy=False)

    def action_add_only(self):
        self.ensure_one()
        vals = {
            'request_id': self.request_id.id,
            'request_form_id': self._context['active_id'],
            'keterangan': self.keterangan,
        }
        self.env['eps.request.form.line'].suspend_security().create(vals)
    
    def action_add_and_more(self):
        self.ensure_one()
        vals = {
            'request_id': self.request_id.id,
            'request_form_id': self._context['active_id'],
            'keterangan': self.keterangan,
        }
        self.create(vals)
        form_id = self.env.ref('eps_request_form.eps_request_form_line_form_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Form Line',
            'view_id': False,
            'views': [(form_id,'form')],
            'view_mode': 'form',
            'res_model': 'eps.request.form.line',
            'target': 'new',
            'view_type': 'form',
            'context': {
                'active_id': self._context['active_id'],
                'readonly_by_pass': True
            }
        }

class RequestFormApproval(models.Model):
    _name = "eps.request.form.approval"
    _description = "Approval Request Form"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()
    
    # 8: fields
    # name = fields.Char(string='Name')
    date = fields.Date(string='Date',readonly=True, default=_get_default_date)
    tanggal_approved = fields.Date(string='Tanggal Approve', readonly=True)
    tanggal_reject = fields.Date(string='Tanggal Reject', readonly=True)
    sequence = fields.Integer(string='Sequence')
    state = fields.Selection(string='State', selection=[('open','Open'),('rejected','Rejected'),('approved','Approved'),],default='open')
    alasan_reject = fields.Text(string='Alasan Reject')
    job_level = fields.Selection(selection=[
        ('1','Clerk'),
        ('2','Staff'),
        ('3','Supervisor'),
        ('4','Manager'),
        ('5','OM / GM / SM'),
        ('6','CHIEF / VICE PRESIDENT')],  string="Level Job",  help="")

    # 8: relation fields
    user_id = fields.Many2one(comodel_name='res.users',string='Approval by')
    employee_id = fields.Many2one(comodel_name='hr.employee',string='Name')
    job_id = fields.Many2one(comodel_name='hr.job',string='Jabatan')
    group_id = fields.Many2one(comodel_name='res.groups')
    request_form_line_id = fields.Many2one(comodel_name='eps.request.form.line', string='Request Form')

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    @api.onchange('employee_id')
    def _change_job_user(self):
        self.user_id = self.employee_id.user_id.id
        self.job_id = self.employee_id.job_id.id
        self.job_level = self.employee_id.job_id.job_level
    
    @api.onchange('job_level')
    def _change_group_by_level(self):
        
        name_job_level = False
        if self.job_level == '1':
            name_job_level = 'CLERK'
        elif self.job_level == '2':
            name_job_level= 'STAFF'
        elif self.job_level == '3':
            name_job_level = 'SUPERVISOR'
        elif self.job_level == '4':
            name_job_level = 'MANAGER'
        elif self.job_level == '5':
            name_job_level = 'OM/GM/SM'
        elif self.job_level == '6':
            name_job_level = 'CHIEF/VICE PRECIDENT'
        group_obj = self.env['res.groups'].suspend_security().search([('name','=', name_job_level)])
        if name_job_level == 'CLERK':
            self.group_id = group_obj.id
        elif name_job_level == 'STAFF':
            self.group_id = group_obj.id
        elif name_job_level == 'SUPERVISOR':
            self.group_id = group_obj.id
        elif name_job_level == 'MANAGER':
            self.group_id = group_obj.id
        elif name_job_level == 'OM/GM/SM':
            self.group_id = group_obj.id
        elif name_job_level == 'CHIEF/VICE PRECIDENT':
            self.group_id = group_obj.id
        name_job_level = False
        self.job_level = self.job_level
    
        

    def action_reject_form(self):
        write = self.write({
            'state':'rejected',
            'tanggal_reject': self._get_default_date(),
            'alasan_reject': self.alasan_reject
        })
        if write:
            self.env['eps.request.form'].suspend_security().write({
                'state': 'rejected'
            })
