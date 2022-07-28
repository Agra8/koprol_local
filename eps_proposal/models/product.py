from odoo import api, fields, models
from odoo.exceptions import ValidationError
import base64
import json
import requests
from odoo.http import request
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
from pytz import timezone

class ProductCategory(models.Model):
    _inherit = "product.category"

    proposal_categ_id = fields.Many2one('eps.category', string='Proposal Category')
    tops_parent_id = fields.Integer('TOPS Category Level 2 ID')
    asset_category_id = fields.Many2one('account.asset.asset', string='Asset Category')
    is_asset_building = fields.Boolean('Asset Building')
    
    @api.model
    def create(self,vals):
        ids = super(ProductCategory,self).create(vals)
        if not vals.get('tops_parent_id',False):  
            vals['tops_parent_id'] = ids.id
        return ids

class Product(models.Model):
    _inherit = "product.product"

    def push_to_tops(self):
        for rec in self:
            rec.product_tmpl_id.push_to_tops()

class ProductProduct(models.Model):
    _inherit = "product.template"

    def start_end_date_request(self):
        start_end_date = fields.Datetime.now()
        return start_end_date

    tops_product_id = fields.Integer('TOPS Product ID', copy=False)
    status_api = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('not_found','not_found'),
        ('done','Done')],string="API Product",default='draft')
    action_api = fields.Selection([
        ('ADD','ADD'),
        ('EDIT','EDIT')
        ], string='Action API')

    state = fields.Selection(selection=[('draft','Draft'),('waiting_for_approval','Waiting for Approval'),('approved','Approved')], default='draft',  string='State',  help='', tracking=True)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','product.template')], copy=False)

   
    def get_tops_product_id(self):
        query = """
                select coalesce(max(tops_product_id),0) from product_template
            """ 
        self._cr.execute (query)
        max = self._cr.fetchall()
        sequence= max[0][0]+1
        return sequence

    def action_request_approval(self):
        koprol_setting = self.env['eps.koprol.setting'].sudo().search([])
        value = 6
        if self.action_api=='U':
            value = 5

        if not koprol_setting:
            raise ValidationError('Konfigurasi registrasi product belum lengkap, silahkan setting terlebih dahulu')
        self.env['eps.matrix.approval.line'].with_context(company_id=koprol_setting.default_company_product_approval_id.id,
            branch_id=koprol_setting.default_branch_product_approval_id.id,
            divisi_id=koprol_setting.default_divisi_product_approval_id.id,
            ).request_by_value(self, value)
        self.write({'state':'waiting_for_approval', 'approval_state':'rf'})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))
    
    
    @api.model
    def create(self,vals):
        if not vals.get('action_api',False):
            vals['action_api'] = 'ADD'
        vals['tops_product_id'] = self.sudo().get_tops_product_id()
        ids = super(ProductProduct,self).create(vals)
        return ids

    def write(self,vals):
        if (vals.get('default_code') or vals.get('name') or vals.get('categ_id') or vals.get('active')) and self.status_api=='done':
            vals['action_api'] = 'EDIT'
            vals['status_api'] = 'draft'
        return super(ProductProduct,self).write(vals)

    def push_to_tops(self):
        for rec in self.filtered(lambda x:x.status_api in ('error','draft')):
            config = self.env['eps.b2b.api.configuration'].sudo().check_config('tops')
            if not config :
                raise ValidationError("Config B2B belum dibuat")
            url = config.base_url
            uid = request.session.uid
            # self.validity_check_api()
            # key = self.company_id.unilife_api_key
            end_point = '/goods_lv_3.php'
            payload = {}
            files = [

            ]
            headers = {
              'api_key': config.api_key,
              'Content-Type': 'application/json',
            }

            vals = self._prepare_data_api()
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
                # response.close()
                    
            

    def _prepare_data_api(self):
        action = self.action_api
        code = self.default_code
        ID = self.tops_product_id
        description = self.name
        parent_id = self.categ_id.tops_parent_id
        price_per_piece = 0
        unit = 'UNIT'
        if self.active:
            is_active = 1
        else:
            is_active = 0
        if self.categ_id.is_asset_building:
            is_asset_building = 1
        else:
            is_asset_building = 0
        
        if self.categ_id.asset_category_id:
            is_asset = 1
            is_asset_numbering = 1
        else:
            is_asset = 0
            is_asset_numbering = 0

        body_raw = {
            "Code": code,
            "ID": ID,
            "Description": description,
            "ParentID":parent_id,
            "PricePerPiece":price_per_piece,
            "unit":unit,
            "IsActive":is_active,  # 0 untuk soft delete  
            "IsAssetNumbering":is_asset_numbering,
            "Flag":action,  # ADD / EDIT
            "IsAsset":is_asset,
            "IsAssetBuilding":is_asset_building
        }

        return json.dumps(body_raw)

    def push_to_tops_by_cron(self):
        records = self.search([('status_api','in',('draft','error'))])
        for record in records:
            record.push_to_tops()


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    initiatives_line_id = fields.Many2one('eps.initiatives.line', string='Initiatives Lines')
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives')