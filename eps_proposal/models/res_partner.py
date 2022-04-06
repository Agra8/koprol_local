from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Partner(models.Model):
    _inherit = "res.partner"

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


    def action_request_approval(self):
        koprol_setting = self.env['eps.koprol.setting'].search([])
        if not koprol_setting:
            raise ValidationError('Konfigurasi registrasi vendor belum lengkap, silahkan setting terlebih dahulu')
        self.env['eps.matrix.approval.line'].with_context(company_id=koprol_setting.default_company_vendor_approval_id.id,
            branch_id=koprol_setting.default_branch_vendor_approval_id.id,
            divisi_id=koprol_setting.default_divisi_vendor_approval_id.id,
            ).request_by_value(self, 5)
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

class PartnerBank(models.Model):
    _inherit = "res.partner.bank"

    surat_pernyataan_kepemilikan_rekening_doc = fields.Binary('Surat Pernyataan Kepemilikah Rekening File')
    fc_buku_tabungan_doc = fields.Binary('Foto Copy Buku Tabungan')
    surat_pernyataan_kepemilikan_rekening_doc_name = fields.Char()
    fc_buku_tabungan_doc_name = fields.Char('')