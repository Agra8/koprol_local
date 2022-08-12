from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import json
import requests
from odoo.http import request
from dateutil.relativedelta import relativedelta
from datetime import datetime

class Partner(models.Model):
    _inherit = "res.partner"

    def start_end_date_request(self):
        start_end_date = fields.Datetime.now()
        return start_end_date

    state = fields.Selection(selection=[('draft','Draft'),('waiting_for_approval','Waiting for Approval'),('approved','Approved')], default='draft',  string='State',  help='', tracking=True)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','res.partner')], copy=False)
    nik = fields.Char('NIK', tracking=True)
    vat = fields.Char('NPWP', tracking=True)
    pkp = fields.Boolean(string="ID PKP", tracking=True)
    tax_address = fields.Char('Tax Address', tracking=True)
    tax_name = fields.Char('Tax Name', tracking=True)
    kode_transaksi = fields.Selection([
            ('01', '01 Kepada Pihak yang Bukan Pemungut PPN (Customer Biasa)'),
            ('02', '02 Kepada Pemungut Bendaharawan (Dinas Kepemerintahan)'),
            ('03', '03 Kepada Pemungut Selain Bendaharawan (BUMN)'),
            ('04', '04 DPP Nilai Lain (PPN 1%)'),
            ('06', '06 Penyerahan Lainnya (Turis Asing)'),
            ('07', '07 Penyerahan yang PPN-nya Tidak Dipungut (Kawasan Ekonomi Khusus/ Batam)'),
            ('08', '08 Penyerahan yang PPN-nya Dibebaskan (Impor Barang Tertentu)'),
            ('09', '09 Penyerahan Aktiva ( Pasal 16D UU PPN )'),
        ], string='Kode Transaksi', help='Dua digit pertama nomor pajak', tracking=True)
    country_code = fields.Char(related='country_id.code', string='Country Code')
    ecommerce = fields.Boolean('Platform Ecommerce')
    siup = fields.Char('SIUP')
    siup_validity = fields.Date('Masa Berlaku SIUP')
    siup_doc = fields.Binary('SIUP File', attachment=True)
    siup_doc_name = fields.Char('SIUP File')
    company_profile_doc = fields.Binary('Company Profile File', attachment=True)
    company_profile_doc_name = fields.Char()
    ktp_doc = fields.Binary('KTP File', attachment=True)
    ktp_doc_name = fields.Char()
    vat_doc = fields.Binary('NPWP File', attachment=True)
    vat_doc_name = fields.Char()
    sppkp_doc = fields.Binary('SPPKP File', attachment=True)
    sppkp_doc_name = fields.Char('SPPKP File')
    akta_pendirian_perusahaan = fields.Char('No. Akta Pendirian Perusahaan')
    akta_pendirian_perusahaan_doc = fields.Binary('Akta Pendirian Perusahaan File', attachment=True)
    akta_pendirian_perusahaan_doc_name = fields.Char()
    nib = fields.Char('NIB')
    nib_validity = fields.Date('Masa Berlaku NIB')
    nib_doc = fields.Binary('NIB File', attachment=True)
    nib_doc_name = fields.Char()
    vendor_registration_doc = fields.Binary('Vendor Registration Form File', attachment=True)
    vendor_registration_doc_name = fields.Char()    

    # TOPS
    is_supplier_showroom = fields.Boolean('Supplier Showroom')
    is_supplier_bengkel = fields.Boolean('Supplier Bengkel')
    is_supplier_umum = fields.Boolean('Supplier Umum', default=True)
    status_api = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('not_found','not_found'),
        ('done','Done')],string="API Vendor",default='draft')
    action_api = fields.Selection([
        ('I','ADD'),
        ('U','EDIT'),
        ('D','DELETE'),
        ], string='Action API')
    code = fields.Char('Vendor Code')

    def get_sequence(self):
        seq_name = 'KOPROL VENDOR CODE'
        seq = self.env['ir.sequence']
        ids = seq.sudo().search([('name','=',seq_name)])
        if not ids:
            prefix = 'STK'
            ids = seq.create({'name':seq_name,
                                'implementation':'standard',
                                'prefix':prefix,
                                 'padding':8})
        return ids.next_by_id()

    @api.model
    def create(self,vals):
        if not vals.get('action_api',False):
            vals['action_api'] = 'I'
        if not vals.get('code',False):
            vals['code'] = self.sudo().get_sequence()
        ids = super(Partner,self).create(vals)
        return ids

    def write(self,vals):
        if (vals.get('code') or vals.get('name') or vals.get('child_ids') or vals.get('street')\
        or vals.get('phone')\
        or vals.get('mobile')\
        or vals.get('bank_ids')\
        or vals.get('email')\
        or vals.get('website')\
        or vals.get('vat')\
        or vals.get('zip')\
        or vals.get('is_supplier_showroom')\
        or vals.get('is_supplier_bengkel')\
        or vals.get('is_supplier_umum')\
        or vals.get('nib_validity')) and self.status_api=='done':

            vals['action_api'] = 'U'
            vals['status_api'] = 'draft'
        return super(Partner,self).write(vals)


    def action_request_approval(self):
        koprol_setting = self.env['eps.koprol.setting'].sudo().search([])
        value = 6
        if self.action_api=='U':
            value = 5

        if not koprol_setting:
            raise ValidationError('Konfigurasi registrasi vendor belum lengkap, silahkan setting terlebih dahulu')
        self.env['eps.matrix.approval.line'].with_context(company_id=koprol_setting.default_company_vendor_approval_id.id,
            branch_id=koprol_setting.default_branch_vendor_approval_id.id,
            divisi_id=koprol_setting.default_divisi_vendor_approval_id.id,
            ).request_by_value(self, value)
        self.write({'state':'waiting_for_approval', 'approval_state':'rf'})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Tidak bisa hapus data dalam status selain draft!'))
        return super(Partner, self).unlink()

    def action_set_draft(self):
        for record in self:
            record.write({'state':'draft'})

    def push_to_tops(self):
        for rec in self.filtered(lambda x:x.status_api in ('error','draft')):
            # self.validity_check_api()
            config = self.env['eps.b2b.api.configuration'].sudo().check_config('tops')
            if not config :
                raise ValidationError("Config B2B belum dibuat")
            url = config.base_url
            uid = request.session.uid
            # self.validity_check_api()
            # key = self.company_id.unilife_api_key
            end_point = '/supplier.php'
            payload = {}
            files = [

            ]
            headers = {
              'api_key': config.api_key,
              'Content-Type': 'application/json',
            }

            vals = self._prepare_data_api()
            print (vals,"<<<<<<<<<<<<<<<<<<<")
            request_time = self.start_end_date_request()
            response = requests.get(url+end_point, data = vals,headers=headers,verify=True)
            status_code = (response.status_code)
            content = json.loads(response.content)
            status = content.get('status',False)
            message = content.get('message',False) 
            ip_address=request.httprequest.headers.environ['REMOTE_ADDR']

            response_time=False
            
            if status_code == 200:
                response_time = self.start_end_date_request()
                if status == "success" :
                    self.env['eps.api.log'].sudo().create_log_api(status_code,status,message,message,uid,vals,response,end_point,ip_address,request_time,response_time)
                    self.write({'action_api':False,'status_api':'done'})
                else :
                    self.env['eps.api.log'].sudo().create_log_api(status_code,status,message,message,uid,vals,response,end_point,ip_address,request_time,response_time)
                    self.write({'status_api':'error'})
            else :
                response_time = self.start_end_date_request()
                self.env['eps.api.log'].sudo().create_log_api(status_code,status,message,message,uid,vals,response,end_point,ip_address,request_time,response_time)
                self.write({'status_api':'error'})
            

    def test_push_to_tops(self):
        for rec in self:
            # self.validity_check_api()
            config = self.env['eps.b2b.api.configuration'].sudo().check_config('tops')
            if not config :
                raise ValidationError("Config B2B belum dibuat")
            url = config.base_url
            uid = request.session.uid
            # self.validity_check_api()
            # key = self.company_id.unilife_api_key
            end_point = '/tes.php'
            payload = {}
            files = [

            ]
            headers = {
              'api_key': config.api_key,
              'Content-Type': 'application/json',
            }

            response = requests.get(url+end_point, headers=headers,verify=True)
            status_code = (response.status_code)
            content = json.loads(response.content)
            status = content.get('status',False)
            message = content.get('message',False) 
            ip_address=request.httprequest.headers.environ['REMOTE_ADDR']

            response_time=False
            
            if status_code == 200:
                response_time = self.start_end_date_request()
                raise ValidationError('Berhasil')
            else :
                raise ValidationError('Error')
            
        return True

    def _prepare_data_api(self):
        SupplierID = self.code
        action = self.action_api
        CompanyName = self.name
        if self.child_ids:
            ContactName = self.child_ids[0].name
            ContactTitle = self.child_ids[0].title.name or 'Bpk.'
        else:
            ContactName = self.name
            ContactTitle = self.title.name or 'Bpk.'
        Address = self.street or ''
        Phone = self.phone or ''
        Mobile = self.mobile or ''
        if self.bank_ids and len(self.bank_ids)==1:
            AccountBank = self.bank_ids[0].bank_id.bic
            AccountName = self.bank_ids[0].acc_holder_name
            AccountNumber = self.bank_ids[0].acc_number
            BankBranch = self.bank_ids[0].branch
        else:
            AccountBank = ''
            AccountName = ''
            AccountNumber = ''
            BankBranch = ''
        EMail = self.email or ''
        HomePage = self.website or ''
        NPWP = self.vat or ''
        PostalCode = self.zip or ''
        # PKPDate = self.
        SupplierShowroom = 1 if self.is_supplier_showroom else 0
        JenisBarang = 'Barang'
        SupplierVerifikasi = 'C'
        SupplierBengkel = 1 if self.is_supplier_bengkel else 0
        SupplierUmum = 1 if self.is_supplier_umum else 0
        
        if self.bank_ids and len(self.bank_ids)==2:
            AccountBank2 = self.bank_ids[1].bank_id.bic
            AccountName2 = self.bank_ids[1].acc_holder_name
            AccountNumber2 = self.bank_ids[1].acc_number
            BankBranch2 = self.bank_ids[1].branch
        else:
            AccountBank2 = ''
            AccountName2 = ''
            AccountNumber2 = ''
            BankBranch2 = ''

        if self.bank_ids and len(self.bank_ids)==3:
            AccountBank3 = self.bank_ids[2].bank_id.bic
            AccountName3 = self.bank_ids[2].acc_holder_name
            AccountNumber3 = self.bank_ids[2].acc_number
            BankBranch3 = self.bank_ids[2].branch
        else:
            AccountBank3 = ''
            AccountName3 = ''
            AccountNumber3 = ''
            BankBranch3 = ''

        PKPDate = str((datetime.today() + relativedelta(years=10)).strftime('%Y-%m-%d')) 
        ExpDate = str((datetime.today() + relativedelta(years=10)).strftime('%Y-%m-%d')) 


        body_raw = {
        'SupplierID': SupplierID,
        'CompanyName': CompanyName,
        'ContactName':ContactName,
        'ContactTitle':ContactTitle,
        'Address': Address,
        'Phone': Phone,
        'Fax': Phone,
        'Mobile': Mobile,
        'HomePage': HomePage,
        'AccountBank': AccountBank,
        'AccountName': AccountName,
        'AccountNumber':AccountNumber,
        'EMail':EMail,
        'ParentSupplier':'',
        'SupplierState':'1',
        'NPWP':NPWP,
        'BankBranch':BankBranch,
        'PostalCode':PostalCode,
        'TaxRateID':'0',
        'UpdateFlag': action, # I: insert, U: Update, D:Delete
        'KelengkapanData': 'N',
        'PKPDate':PKPDate,
        'OperationalAddress':'',
        'SupplierShowroom':SupplierShowroom,
        'JenisBarang':JenisBarang, # Barang/Jasa
        'SupplierVerifikasi':'N',
        'SupplierBengkel':SupplierBengkel,
        'SupplierUmum':SupplierUmum,
        'AccountBank2':AccountBank2,
        'AccountName2':AccountName2,
        'AccountNumber2':AccountNumber2,
        'AccountBank3':AccountBank3,
        'AccountName3':AccountName3,
        'AccountNumber3':AccountNumber3,
        'BankBranch2':BankBranch2,
        'BankBranch3':BankBranch3,
        'ExpDate':ExpDate,

        }
        return json.dumps(body_raw)

    def push_to_tops_by_cron(self):
        records = self.search([('status_api','in',('draft','error'))])
        for record in records:
            record.push_to_tops()

class PartnerBank(models.Model):
    _inherit = "res.partner.bank"

    surat_pernyataan_kepemilikan_rekening_doc = fields.Binary('Surat Pernyataan Kepemilikah Rekening File')
    fc_buku_tabungan_doc = fields.Binary('Foto Copy Buku Tabungan')
    surat_pernyataan_kepemilikan_rekening_doc_name = fields.Char()
    fc_buku_tabungan_doc_name = fields.Char('')
    branch = fields.Char('Branch')