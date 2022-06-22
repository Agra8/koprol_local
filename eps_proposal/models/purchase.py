from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import subprocess
import base64
import os
import platform
from odoo.tools import config
from datetime import datetime, date, timedelta
import qrcode
from werkzeug.urls import url_encode
from io import BytesIO
import pytz
from pytz import timezone
import json
import requests
from odoo.http import request

class Purchase(models.Model):
    _inherit = "purchase.order"

    def start_end_date_request(self):
        start_end_date = fields.Datetime.now()
        return start_end_date

    branch_id = fields.Many2one('res.branch', string='Branch', required=True, tracking=True, domain="[('company_id','=',company_id)]")
    divisi_id = fields.Many2one('eps.divisi', string='Divisi', required=True, tracking=True, domain="[('company_id','=',company_id)]")
    department_id = fields.Many2one('hr.department', domain="[('company_id','=',company_id)]", string='Department', required=True, tracking=True)
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives')
    status_api = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('not_found','not_found'),
        ('done','Done')],string="API Status",default='draft')
    tops_po_number = fields.Char("TOPS PO Number")
    tops_pr_number = fields.Char("TOPS PR Number")

    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].sudo().get_per_branch(vals['branch_id'], 'PO')
        ids = super(Purchase,self).create(vals)    
        return ids

    def push_to_tops(self):
        for rec in self:
            config = self.env['eps.b2b.api.configuration'].sudo().check_config('tops')
            if not config :
                raise ValidationError("Config B2B belum dibuat")
            url = config.base_url
            uid = request.session.uid
            # self.validity_check_api()
            # key = self.company_id.unilife_api_key
            end_point = '/post_pr_po.php'
            payload = {}
            files = [

            ]
            headers = {
              'api_key': config.api_key,
              'Content-Type': 'application/json',
            }

            vals = self._prepare_data_api()
            # print (vals,"<<<<<<<<<<<<<<<<<<<<<<")
            # wkwkwk
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
                    tops_po_number = ''
                    tops_pr_number = ''
                    self.env['eps.api.log'].sudo().create_log_api(status_code,status,message,message,uid,vals,response,end_point,ip_address,request_time,response_time)
                    if content.get('data',False):
                        if content.get('data').get('summary',False):
                            tops_po_number = content.get('data').get('summary').get('po_number',False)
                            tops_pr_number = content.get('data').get('summary').get('pr_number',False)

                    self.write({'status_api':'done','tops_po_number':tops_po_number,'tops_pr_number':tops_pr_number})
                else :
                    self.env['eps.api.log'].sudo().create_log_api(status_code,status,message,message,uid,vals,response,end_point,ip_address,request_time,response_time)
                    self.write({'status_api':'error'})
            else :
                response_time = self.start_end_date_request()
                self.env['eps.api.log'].sudo().create_log_api(status_code,status,message,message,uid,vals,response,end_point,ip_address,request_time,response_time)
                self.write({'status_api':'error'})
                # response.close()
                    

    def _prepare_data_api(self):
        Items = []
        QuotationDetails = []
        QuotationID = []
        ItemIDLevel3 = []
        TotalItem = 0
        ItemQty = []

        for line in self.order_line:
            QuotationID.append(line.initiatives_line_id.quotation_line_id.quotation_id.name or line.initiatives_line_id.initiatives_id.name)
            ItemIDLevel3.append(line.product_id.tops_product_id)
            TotalItem+=line.product_qty
            ItemQty.append(int(line.product_qty))

            Items.append({
                "ID": line.product_id.tops_product_id, 
                "Code": line.product_id.default_code or '',
                "Description": line.product_id.name,
                "ParentID": line.product_id.categ_id.tops_parent_id,
                "PricePerPiece": line.price_unit,
                "unit": "UNIT",
                "IsActive": 1 if line.product_id.active else 0,
                "IsAssetNumbering": 1 if line.product_id.categ_id.asset_category_id else 0,
                "IsAsset": 1 if line.product_id.categ_id.asset_category_id else 0,
                "IsAssetBuilding": 1 if line.product_id.categ_id.is_asset_building else 0,
                "Flag": "EDIT"
                })

            if line.product_id.type=='consu':
                QuotationDetails.append({
                   'QuotationID': line.initiatives_line_id.quotation_line_id.quotation_id.name or line.initiatives_line_id.initiatives_id.name,
                    'SupplierID': self.partner_id.code,
                    'Validity': str(line.initiatives_line_id.quotation_line_id.quotation_id.validity_date or line.initiatives_line_id.initiatives_id.date),
                    'ItemPrice': line.initiatives_line_id.quotation_line_id.price_unit or line.initiatives_line_id.price_unit,
                    'ItemIDLevel3': line.product_id.tops_product_id,
                    'ItemPPN': line.initiatives_line_id.quotation_line_id.price_tax or line.initiatives_line_id.price_tax,
                    'DiscPercent': line.initiatives_line_id.quotation_line_id.discount or line.initiatives_line_id.discount,
                    'ItemDisc': 0.00,
                    'Jasa': 0.00,
                    'Remarks': '',
                    })
            elif line.product_id.type=='service':
                QuotationDetails.append({
                   'QuotationID': line.initiatives_line_id.quotation_line_id.quotation_id.name or line.initiatives_line_id.initiatives_id.name,
                    'SupplierID': self.partner_id.code,
                    'Validity': str(line.initiatives_line_id.quotation_line_id.quotation_id.validity_date or line.initiatives_line_id.initiatives_id.date),
                    'ItemPrice': 0.00,
                    'ItemIDLevel3': line.product_id.tops_product_id,
                    'ItemPPN': line.initiatives_line_id.quotation_line_id.price_tax or line.initiatives_line_id.price_tax,
                    'DiscPercent': line.initiatives_line_id.quotation_line_id.discount or line.initiatives_line_id.discount,
                    'ItemDisc': 0.00,
                    'Jasa': line.initiatives_line_id.quotation_line_id.price_unit or line.initiatives_line_id.price_unit,
                    'Remarks': '',
                    })
        PR_PO_Data = {
            'EntityID':self.company_id.tops_id,
            'BranchID':self.branch_id.tops_id,
            'BusinessID':self.company_id.business_id.tops_id,
            'BSDivisionID':self.divisi_id.tops_id,
            'DepartmentID':self.department_id.tops_id,
            'Dibuat_Di':self.branch_id.kabupaten_id.name or '', #Sesuai Cabang (TBC Mas Raksa)
            'Pemohon':'KORPOL', # user CreatedBy
            'Notes':self.notes or '',
            'IsadvancePayment':'0',
            'IsDemoCar':'0',
            'QuotationID': ",".join(str(x) for x in list(dict.fromkeys(QuotationID))),
            'ItemIDLevel3': ",".join(str(x) for x in list(ItemIDLevel3)), # list item dg separator coma 
            'ItemQty': ",".join(str(x) for x in list(ItemQty)), # qty item 2 (qty dari 13579),3 (qty dari 13578)
            'TotalItem':len(ItemQty), # jml total item 2 (13579 & 13578)
            'RequestType':'1', #Request Type (TBC Mas Raksa)
            'Termin':self.payment_term_id.no_of_installment, # ex: 6
        }
            
        body_raw = {
        'PR_PO_Data' : PR_PO_Data,
        'QuotationDetails': QuotationDetails,
        'Items': Items

        }
        return json.dumps(body_raw)

    def push_to_tops_by_cron(self):
        records = self.search([('status_api','in',('draft','error'))])
        for record in records:
            record.push_to_tops()

class PurchaseLine(models.Model):
    _inherit = "purchase.order.line"

    branch_id = fields.Many2one('res.branch', string='Branch', required=True, tracking=True, domain="[('company_id','=',company_id)]")
    initiatives_line_id = fields.Many2one('eps.initiatives.line', string='Initiatives')