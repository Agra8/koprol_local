#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
import string, random, cryptocode, os
from cryptography.fernet import Fernet

# 3:  imports of odoo
from typing import Sequence
from odoo import models, fields, api
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

# 4:  imports from odoo modules
from odoo.exceptions import Warning

# 5: local imports

# 6: Import of unknown third party lib

class RequestForm(models.Model):
    _name="dms.request.form"
    _description="Request Form for JRF / ARF"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    
    def _key_gen(self):
        key_len = 5
        random_letters = string.ascii_letters+string.digits
        keylist = [random.choice(random_letters) for i in range (key_len)]
        return ("".join(keylist))


    # 8: fields
    name = fields.Char(string='Name', index=True)
    date = fields.Date(string='Date', readonly=True,default=_get_default_date)
    is_maindealer = fields.Boolean(string='Main Dealer')
    state = fields.Selection(string='State', selection=[('draft','Draft'),('open','Open'),('confirmed','Confirmed')])
    alasan_reject = fields.Text(string='Alasan Reject')
    total_approval = fields.Float(string='Approval Percentage', compute='_compute_total_approval')
    name_pegawai = fields.Char(string='Nama Pegawai')
    no_telp = fields.Char(string="Nomor Telp")
    state = fields.Selection(string='State', selection=[('draft','Draft'), ('rfa','Waiting for Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'),('cancel', 'Cancel'),('open', 'Open'), ('closed', 'Closed')], default='draft')
    email_penerima = fields.Char()
    penerima = fields.Char()
    token_penerima = fields.Char()
    approval_url = fields.Char()
    reject_url = fields.Char()
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
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')
    employee_id = fields.Many2one(comodel_name='hr.employee',string='Employee')
    approval_ids = fields.One2many(comodel_name='dms.request.form.approval',inverse_name='request_form_id', string='Approval JRF/ARF')
    request_line_ids = fields.One2many(comodel_name='dms.request.form.line',inverse_name='request_form_id', string='Request')
    job_title = fields.Many2one(comodel_name='hr.job',string='Job Title')


    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.branch'].suspend_security().browse(vals['branch_id'])
            doc_code = branch_obj.code
            vals['name'] = self.env['ir.sequence'].suspend_security().get_per_doc_code(doc_code,'RF')
            
            if branch_obj.is_md == True:
                department_obj = self.env['hr.department'].suspend_security().browse(vals['department_id'])
                job_level = department_obj.manager_id.job_id.job_level 
                group_id = self._change_group_by_level(job_level if job_level else '4')
                record = {
                    'employee_id': department_obj.manager_id.id,
                    'job_id': department_obj.manager_id.job_id.id,
                    'job_level': job_level,
                    'group_id': group_id,
                    'state': 'open',
                }
                create_super = super(RequestForm, self).create(vals)
                create = self.env['dms.request.form.approval'].suspend_security().create(record)
                record['request_form_id'] = create_super.id
                record['user_id'] = create.employee_id.user_id.id
                create.suspend_security().write(record)
            elif branch_obj.is_md == False:
                job_level = branch_obj.kacab_id.job_id.job_level
                group_id = self._change_group_by_level(job_level if job_level else '3')
                record = {
                    'employee_id': branch_obj.kacab_id.id,
                    'job_id': branch_obj.kacab_id.job_id.id,
                    'job_level': job_level,
                    'group_id': group_id,
                    'state': 'open',
                }
                create_super = super(RequestForm, self).create(vals)
                create = self.env['dms.request.form.approval'].suspend_security().create(record)
                record['request_form_id'] = create_super.id
                record['user_id'] = create.employee_id.user_id.id
                create.suspend_security().write(record)
                  
        return create_super
    
    def unlink(self):
        raise Warning('Request Form tidak bisa di delete !')
    
    def copy(self):
        raise Warning('Perhatian!\nData tidak bisa diduplikasi.')


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

    def action_rfa(self):
        template = self.env.ref('dms_request_form.template_mail_request_form_result')
        mail = self.env['mail.template'].suspend_security().browse(template.id)
        for user in self.approval_ids.employee_id:
            self.email_penerima = user.work_email
            self.penerima = user.name
            self.token_penerima = self.create_token(self.id, user.id)
            path = "/approval/%s" % self.token_penerima
            path_reject = "/reject/%s" % self.token_penerima
            self.approval_url = self.get_url() + path
            self.reject_url = self.get_url() + path_reject
            mail.send_mail(self.id, force_send=True)
        if mail:
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

    @api.depends('approval_ids','approval_ids.state')
    def _compute_total_approval(self):
        for record in self:
            total = 0.0
            if len(record.approval_ids):
                approved = record.approval_ids.suspend_security().search([
                    ('request_form_id','=',record.id),
                    ('state','=','approved')
                    ])
                total = float(len(approved)) / float(len(record.approval_ids))
            record.total_approval = total*100
    
    def action_request(self):
        self.ensure_one()
        form_id = self.env.ref('dms_request_form.dms_request_form_line_form_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Form Line',
            'view_id': False,
            'views': [(form_id,'form')],
            'view_mode': 'form',
            'res_model': 'dms.request.form.line.wizard',
            'target': 'new',
            'view_type': 'form',
            'context': {
                'active_id': self.id
            }
        }
    
    def action_approve(self):
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
       
        approval_open = self.approval_ids.search([
            ('request_form_id', '=', self.id),
            ('state', '=', 'open')
        ])
        if not approval_open:
            self.write({
                'state': 'approved'
            })
    
    def action_reject(self):
        approval = self._check_user_groups()
        form_id = self.env.ref('dms_request_form.dms_request_form_approval_reject_form').id
        return {
            'name': ('Alasan Reject'),
            'res_model': 'dms.request.form.approval',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': approval.id
        }
      
    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })
        
            
    def _check_user_groups(self):
        approval_obj = self.approval_ids.search([
            ('request_form_id', '=', self.id),
            ('state','=','open')
        ])

        for approval in approval_obj:
            # TODO: create check if user already approving with this request
            user_approval_obj = self.approval_ids.search([
                ('request_form_id', '=', self.id),
                ('user_id','=', self.env.user.id),
                ('state', '=','approved')
            ])
            if self.env.user.has_group(approval.group_id.get_xml_id().popitem()[1]) and not user_approval_obj:
                return approval
        
        raise Warning("Anda 'Tidak Dapat' atau 'Sudah' melakukan Approval. \nPeriksa Tab Approval.")
    
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
    
    def dms_request_form_view(self):
        name= 'Request Form'
        tree_id = self.env.ref('dms_request_form.dms_request_form_view_tree').id
        form_id = self.env.ref('dms_request_form.dms_request_form_view_form').id
        search_id = self.env.ref('dms_request_form.dms_request_form_search').id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'dms.request.form',
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
    _name="dms.request.form.line"
    _description="Request Form Line"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    
    def compute_filename(self):
        for record in self:
            if record.filename_upload:
                try:
                    image_lampiran = self.env['dms.conf.image'].suspend_security().get_img(record.filename_upload)
                    record.file_show = image_lampiran
                    if record.type_file == 'pdf':
                        record.file_pdf = image_lampiran
                    else:
                        record.file_pdf = False
                except FileNotFoundError as err:
                    _logger.error(err)
                    record.file_show = False
            
            else:
                record.file_show = False

    # 8: fields

    name=fields.Char(string='Name')
    date=fields.Date(string='Date', default=_get_default_date)
    keterangan = fields.Text(string='Keterangan')
    form_id = fields.Many2one(comodel_name='master.jrf.arf', string='Master Request')
    request_form_id = fields.Many2one(comodel_name='dms.request.form', string='Request Form')
    
    file_upload = fields.Binary(string='Upload Lampiran')
    filename_upload = fields.Char(string='Nama Lampiran Upload')
    filename = fields.Char(string='Nama Lampiran')
    file_show = fields.Binary(string='lampiran_show', compute='compute_filename')
    file_download = fields.Binary(string='Download Lampiran', related='file_show')
    file_pdf = fields.Binary(string='file pdf', compute='compute_filename')
    type_file = fields.Char(string='Tipe File')

    
    @api.model
    def write(self, vals: dict):
        if vals.get('type_file'):
            type_file = vals.pop('type_file')
        
        if vals.get('file_upload'):
            file_upload = vals['file_upload']
            vals['file_upload'] = False
            tmp_lampiran = vals['filename'].split('.')
            filename_up = f'[{self.id}]{type_file}-request_form.{tmp_lampiran[len(tmp_lampiran) - 1]}'
            self.env['dms.conf.image'].suspend_security().upload_file(filename_up, file_upload)
            vals['filename_upload'] = filename_up
        return super(RequestFormLine, self).write(vals)
    
class RequestFormLineWizard(models.TransientModel):
    _name="dms.request.form.line.wizard"
    _description="Request Form Line"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    # 8: fields

    name=fields.Char(string='Name')
    date=fields.Date(string='Date', default=_get_default_date)
    keterangan = fields.Text(string='Keterangan')
    form_id = fields.Many2one(comodel_name='master.jrf.arf', string='Master Request')
    request_form_id = fields.Many2one(comodel_name='dms.request.form', string='Request Form')
    attachment_line_ids = fields.One2many(comodel_name='request.form.attachment', inverse_name='request_line_id')


    def action_add_only(self):
        self.ensure_one()
        vals = {
            'form_id': self.form_id.id,
            'request_form_id': self._context['active_id'],
            'keterangan': self.keterangan,
        }
        self.env['dms.request.form.line'].suspend_security().create(vals)
    
    def action_add_and_more(self):
        self.ensure_one()
        vals = {
            'form_id': self.form_id.id,
            'request_form_id': self._context['active_id'],
            'keterangan': self.keterangan,
        }
        self.create(vals)
        form_id = self.env.ref('dms_request_form.dms_request_form_line_form_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Form Line',
            'view_id': False,
            'views': [(form_id,'form')],
            'view_mode': 'form',
            'res_model': 'dms.request.form.line',
            'target': 'new',
            'view_type': 'form',
            'context': {
                'active_id': self._context['active_id'],
                'readonly_by_pass': True
            }
        }

class RequestFormApproval(models.Model):
    _name = "dms.request.form.approval"
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
    request_form_id = fields.Many2one(comodel_name='dms.request.form', string='Request Form')

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
            self.env['dms.request.form'].suspend_security().write({
                'state': 'rejected'
            })

class RequestFormAttachment(models.Model):
    _name = "request.form.attachment"

    def compute_filename(self):
        for record in self:
            if record.filename_upload:
                try:
                    image_lampiran = self.env['dms.conf.image'].suspend_security().get_img(record._filename_upload)
                    record.file_show = image_lampiran
                    if record.type_file == 'pdf':
                        record.file_pdf = image_lampiran
                    else:
                        record.file_pdf = False
                except FileNotFoundError as err:
                    _logger.error(err)
                    record.file_show = False
            
            else:
                record.file_show = False
    
    file_upload = fields.Binary(string='Upload Lampiran')
    filename_upload = fields.Char(string='Nama Lampiran Upload')
    file = fields.Binary(string='Lampiran')
    filename = fields.Char(string='Nama Lampiran')
    file_show = fields.Binary(string='lampiran_show', compute='compute_filename')
    file_download = fields.Binary(string='Download Lampiran', related='file_show')
    file_pdf = fields.Binary(string='file pdf', compute='compute_filename')
    type_file = fields.Char(string='Tipe File')

    request_line_id = fields.Many2one(comodel_name='dms.request.form.line',string='Request Line', index=True)

    @api.model
    def create(self, vals: dict):
        if not vals.get('file_upload'):
            raise Warning('File tidak boleh kosong !')
        if not vals.get('filename'):
            raise Warning('Filename_upload tidak boleh kosong!')
        
        type_file = ''
        if vals.get('type_file'):
            type_file = vals.pop('type_file')
        
        file_upload = False
        if vals.get('file_upload'):
            file_upload = vals['file_upload']
            vals['file_upload'] = False
        
        ids = super(RequestFormAttachment, self).create(vals)

        if file_upload:
            tmp_lampiran = vals['filename'].split('.')
            filename_up = f'[{ids.id}]{type_file}-{str(vals["request_line_id"])}-request_form.{tmp_lampiran[len(tmp_lampiran) - 1]}'
            self.env['dms.conf.image'].suspend_security().upload_file(filename_up, file_upload)
            ids.filename_upload = filename_up
        return ids
    
    @api.model
    def write(self, vals: dict):
        if vals.get('type_file'):
            type_file = vals.pop('type_file')
        
        if vals.get('file_upload'):
            file_upload = vals['file_upload']
            vals['file_upload'] = False
            tmp_lampiran = vals['filename'].split('.')
            filename_up = f'[{self.id}]{type_file}-{str(vals["request_form"])}-request_form.{tmp_lampiran[len(tmp_lampiran) - 1]}'
            self.env['dms.conf.image'].suspend_security().upload_file(filename_up, file_upload)
            vals['filename_upload'] = filename_up
        return super(RequestFormAttachment, self).write(vals)