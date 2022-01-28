# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models
from odoo.exceptions import Warning
from datetime import datetime, timedelta
import time
import pytz
from pytz import timezone
from validate_email import validate_email

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Branch(models.Model):
    _name = "res.branch"
    _description = 'Branches'
    _order = 'name'

    def _get_company(self):
        res_user = self.env['res.users'].browse(self._uid)
        return res_user.company_id.id

    def get_default_date(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))    
    
    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta')) 

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    # name = fields.Char(related='partner_id.name', string='Branch Name', store=True)
    name = fields.Char(string='Branch Name')
    code = fields.Char(string='Branch Code', required=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,default=_get_company)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    fax = fields.Char(string='Fax')
    email = fields.Char(string='e-mail')
    street = fields.Char(string='Address')
    street2 = fields.Char()
    rt = fields.Char(string='RT',size=3)
    rw = fields.Char(string='RW',size=3)
    state_id = fields.Many2one('res.country.state',string='Province')
    kabupaten_id = fields.Many2one('res.city','Kabupaten')
    kecamatan_id = fields.Many2one('res.kecamatan','Kecamatan', domain="[('city_id','=',kabupaten_id)]")
    kecamatan = fields.Char(string="Kecamatan") 
    kelurahan_id = fields.Many2one('res.kelurahan',string='Kelurahan', domain="[('kecamatan_id','=',kecamatan_id)]")
    kelurahan = fields.Char(string="Kelurahan")
    kode_pos = fields.Char(string="Kode Pos")
    is_pkp = fields.Boolean('PKP')
    is_md = fields.Boolean('Is Main Dealer')
    interco_account_id = fields.Many2one('account.account',string='Intercompany Account')
    interco_match_account_id = fields.Many2one('account.account',string='Intercompany Match Account')
    pimpinan_id = fields.Many2one('hr.employee',string='Pimpinan')
    profit_centre = fields.Char(string='Profit Centre',required=True,help='please contact your Accounting Manager to get Profit Center.')

    # relation fields
    area_id = fields.Many2one(comodel_name='res.area', string='Area', help='')
    parent_id = fields.Many2one(comodel_name='res.branch', string='Parent Branch', help='')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', help='')
    kawil_id = fields.Many2one(comodel_name='hr.employee', string='Kepala Wilayah', domain=[('job_id.sales_force','=','am')])
    owner_id = fields.Many2one(comodel_name='hr.employee', string='Owner')
    kacab_id = fields.Many2one(comodel_name='hr.employee', string='Kepala Cabang', domain=[('job_id.sales_force','=','soh')])
    adh_id = fields.Many2one(comodel_name='hr.employee', string='Admin Head')
    kabeng_id = fields.Many2one(comodel_name='hr.employee', string='Kepala Bengkel')
    kasir_id = fields.Many2one(comodel_name='hr.employee', string='Kasir')
    
    def init(self):
        self._cr.execute("""
            ALTER TABLE IF EXISTS res_branch 
            DROP CONSTRAINT IF EXISTS res_branch_name_code_uniq
            
        """
        )

    #NAME & CODE should unique
    @api.constrains('company_id','name','code')
    def _check_name_code(self):
        for record in self:
            branches = self.search([('company_id','=',record.company_id.id),('name','=',record.name),('code','=',record.code),('id','!=',record.id)])
            if branches:
                raise Warning('Nama dan Code sudah pernah digunakan!')

    @api.model
    def create(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        if vals.get('street'):
            vals['street'] = vals['street'].title()

        partner = self.env['res.partner'].sudo().create({
            'name': vals.get('name'),
            'default_code':vals.get('code'),
            'is_branch': True
        })
        vals['partner_id'] = partner.id

        branch = super(Branch, self).create(vals)

        partner.sudo().write({
            'branch_id': branch.id,
            'company_id': branch.company_id and branch.company_id.id or False,
        })

        return branch

    def write(self, vals):
        if vals.get('street'):
            vals['street'] = vals['street'].title()
        return super(Branch, self).write(vals)

    @api.onchange('state_id')
    def _onchange_province(self):
        self.kabupaten_id = False

    @api.onchange('kabupaten_id')    
    def _onchange_city(self):
        self.kecamatan_id = False

    @api.onchange('kecamatan_id')
    def _onchange_kecamatan(self):
        self.kelurahan_id = False
        if self.kecamatan_id:
            self.kecamatan = self.kecamatan_id.name

    @api.onchange('kelurahan_id')    
    def _onchange_kelurahan(self):
        if self.kelurahan_id:
            self.kelurahan = self.kelurahan_id.name
   
    @api.onchange('email')
    def _onchange_email(self):
        if self.email:
            cek = validate_email(self.email)
            if not cek:
                raise Warning('Email tidak valid, silahkan dicek kembali !')

    @api.constrains('mobile')
    def cek_mobile(self):
        if self.mobile:
            pat_mobile = self.mobile.isdigit()
            if not pat_mobile:
                raise Warning('No Telp tidak boleh mengandung karakter, harus angka !')

    @api.constrains('phone')
    def cek_phone(self):
        if self.phone:
            pat_phone = self.phone.isdigit()
            if not pat_phone:
                raise Warning('No Telp tidak boleh mengandung karakter, harus angka !')

    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        for record in self :
            name = record.name
            if record.code:
                name = "[%s] %s" % (record.code, name)
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|',('name', operator, name),('code', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()

class ir_sequence(models.Model):
    _inherit = 'ir.sequence'

    def get_per_branch(self, branch_id, prefix):
        branch = self.env['res.branch'].browse(branch_id)
        doc_code = branch.code
        company_code = branch.company_id.code
        seq_name = '{0}/{1}/{2}'.format(prefix, company_code, doc_code)

        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            ids = self.create({'name':seq_name,
                                 'implementation':'standard',
                                 'prefix':prefix,
                                 'padding':5})
         
        return ids.next_by_id()

    def get_per_form(self, prefix):
        seq_name = '{0}'.format(prefix)

        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            ids = self.create({'name':seq_name,
                                 'implementation':'standard',
                                 'prefix':prefix,
                                 'padding':5})
         
        return ids.next_by_id()
