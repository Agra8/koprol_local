import itertools
from lxml import etree
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.osv import osv
from odoo.tools.float_utils import float_is_zero, float_compare      
 
class eps_hr_employee (models.Model):
    _inherit = 'hr.employee'
    

    @api.model
    def create(self, vals):
        group_id = False
        if vals.get('job_id'):
            jobs = self.env['hr.job'].sudo().search([('id','=',vals['job_id'])],limit=1)
            if jobs:
                group_id = jobs.group_id.id
        if not group_id and vals.get('is_user',False): 
            raise Warning('Perhatian ! User Group belum diisi di Master Job.')   
        
        if vals['job_id'] :
            job=self.env['hr.job'].search([('id','=',vals['job_id'])])
            if job.name =='Driver' :
                partner = {
                    'name':vals['name'],
                    'driver': True,
                    'mobile': vals.get('mobile_phone',False),
                    'phone': vals.get('work_phone',False),
                    'email': vals.get('work_email',False),
                    'customer': False,                                      
                    }
            elif job.name =='Operator':
                partner = {
                    'name':vals['name'],
                    'operator': True,
                    'mobile': vals.get('mobile_phone',False),
                    'phone': vals.get('work_phone',False),
                    'email': vals.get('work_email',False), 
                    'customer': False,                                     
                    }
            else :
                partner = {
                    'name':vals['name'],
                    # 'customer_rank': 1,
                    # 'supplier_rank': 1,
                    'mobile': vals.get('mobile_phone',False),
                    'phone': vals.get('work_phone',False),
                    'email': vals.get('work_email',False),                                     
                    }
            partner_id=self.env['res.partner'].create(partner)
            vals['partner_id'] = partner_id.id

        create =  super(eps_hr_employee,self).create(vals)
        
        if vals.get('is_user',False):
            area_id = self.env['res.area'].browse(vals['area_id'])
            company_ids = [(4,t.id) for t in area_id.company_ids]
            create_user = self.create_user(vals['name'],vals['user_login'],vals['area_id'],group_id,vals['work_email'],partner_id.id,company_ids,vals['company_id'])
            create.user_id = create_user

        return create

    branch_id = fields.Many2one('res.branch',string='Cabang')
    area_id = fields.Many2one('res.area',string='Area')
    tgl_masuk = fields.Date(string='Mulai Bekerja')
    tgl_keluar = fields.Date(string='Tanggal Keluar')
    bank = fields.Selection([('bca','BCA'),('bri','BRI')],string='Bank')
    no_rekening = fields.Char(string='No. Rekening')
    partner_id = fields.Many2one('res.partner','Partner')
    is_user = fields.Boolean('User') 
    user_login = fields.Char('Login') 
    nip = fields.Char('NIP')
    divisi_id = fields.Many2one('eps.divisi',string='Divisi',domain="[('company_id','=',company_id)]")

    def write(self, vals):
        user_id = False
        if vals.get('name'):
            self.partner_id.write({'name':vals.get('name')})
        if vals.get('work_email'):
            self.partner_id.write({'email':vals.get('work_email')})
        if vals.get('tgl_keluar'):
            self.partner_id.write({'active':False})
        if vals.get('tgl_keluar')==False:
            self.partner_id.write({'active':True})
        
        if vals.get('area_id',False):
            if self.user_id:
                area_id = self.env['res.area'].browse(vals['area_id'])
                self.user_id.write({
                    'area_id' : vals['area_id'],
                    'company_ids' : [(6,0,[t.id for t in area_id.company_ids])]
                })
        
        if vals.get('is_user',False):
            if not self.user_id:
                login = self.nip
                area_id = self.area_id
                name = self.name
                email = self.work_email
                group_id = False
                if vals.get('user_login',False):
                    login = vals['user_login'] 
                if vals.get('area_id',False):
                    # area_id = vals['area_id']
                    area_id = self.env['res.area'].browse(vals['area_id'])
                if vals.get('name',False):
                    name = vals['name'] 
                if vals.get('job_id',False):
                    jobs = self.env['hr.job'].sudo().browse(vals['job_id'])
                    if not jobs.group_id:
                        raise Warning('Perhatian ! User Group belum diisi di Master Job.')    
                    group_id = jobs.group_id.id
                else:
                    if not self.job_id.group_id:
                        raise Warning('Perhatian ! User Group belum diisi di Master Job.')
                    group_id = self.job_id.group_id.id

                if vals.get('email',False):
                    email = vals['email']
                if not email:
                    email = 'user@example.com'
                
                company_ids = [(4,t.id) for t in area_id.company_ids]
                create_user = self.create_user(name,login,area_id.id,group_id,email,self.partner_id.id,company_ids,self.company_id.id)
                if create_user:
                    vals['user_id'] = create_user
        if vals.get('is_user') == False: 
            if self.user_id:
                user_id = self.user_id
        return super(eps_hr_employee, self).write(vals)

    def unlink(self, context=None):
        # raise Warning('Tidak Bisa Hapus Karyawan')
        for record in self:
            if record.partner_id and not record.user_id:
                record.partner_id.unlink()
            if record.user_id:
                record.user_id.unlink()
        return super(eps_hr_employee, self).unlink()
    

    def create_user(self,name,login,area_id,group_id,work_email,partner_id,company_ids,company_id):
        users = self.env['res.users'].sudo().search([
            ('login','=',login),
            '|',
            ('active','=',False),('active','=',True)
        ])        
        if users:
            raise Warning('Perhatian ! \n Username sudah digunakan, silahkan buat username yang uniq.')

        password = login
        if group_id:
            group_id = [(6,0,[group_id])]
        user_create = self.env['res.users'].sudo().create({
           'name':name,
           'login': login,
           'area_id':area_id,
           'password':password,
           'groups_id':group_id,
           'email':work_email,
           'partner_id':partner_id,
           'company_ids':company_ids,
           'company_id': company_id,
        })
        return user_create.id


class EmployeeJob(models.Model):
    _inherit = "hr.job"

    group_id = fields.Many2one('res.groups','Group')


class EmployeeDepartment(models.Model):
    _inherit = "hr.department"

    code = fields.Char(string='Code')
    tops_id = fields.Char('TOPS ID')
