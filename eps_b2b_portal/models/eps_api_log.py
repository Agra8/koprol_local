from odoo import api, fields, models
from datetime import datetime
import time
import pytz
from pytz import timezone

class ApiLog(models.Model):
    _name = "eps.api.log"
    _order = "date desc"

    @api.model
    def _get_default_date(self):
        return fields.Datetime.now()

    user_id = fields.Many2one('res.users', string='User')
    name = fields.Text('Message')
    end_point = fields.Text(string='End Point')
    ip_address = fields.Text(string='IP Address')
    response = fields.Text(string='Response')
    header = fields.Text(string='Header')
    request = fields.Text('Request')
    request_time = fields.Datetime(string='Request Time')
    response_time = fields.Datetime(string='Response Time')
    htttp_response_code = fields.Char(string='Http Response Code')
    status = fields.Char('Status')
    description = fields.Text('Descripton')
    module_name = fields.Char('Module')
    model_name = fields.Char('Model')
    transaction_id = fields.Integer('Transaction ID')
    origin = fields.Char('Origin')
    date = fields.Datetime('Datetime',default=_get_default_date)
    update_uid = fields.Many2one('res.users','Update By')
    insert_uid = fields.Many2one('res.users','Insert By')
    data_count = fields.Integer(string='Data Count')
    method = fields.Selection([('GET','GET'),('POST','POST')],string="Method")
    api_type = fields.Selection(string='API Type', selection=[
        ('normal_api', 'Normal API'), 
        ('b2b', 'B2B'), 
        ('tops', 'TOPS'),
        ('slack','Slack'),
        ('rest_api','Rest Api'),
    ], default='normal_api')
    
    type = fields.Selection([
        ('incoming','Incoming'),
        ('outgoing','Outgoing')],string="Type")
    
    url = fields.Char('URL')
    request_type = fields.Selection([
        ('post','POST'),
        ('get','GET'),
        ('put','PUT'),
        ('delete','Delete')],string="Request Type")
    request = fields.Text('Request')

    # def create_log_api33(self, name,status, type, header,url, end_point,request_type, request, response_code, response, jml_data=False, request_time=False, response_time=False):
    #     print ("xxxxxxxxxxxkjkajdsas")
    #     var=self.create({
    #         'name':name,
    #         'status':status,
    #         'type':type,
    #         'header':header,
    #         'url':url,
    #         'end_point' : end_point,
    #         'request_type':request_type,
    #         'request':request,
    #         'htttp_response_code':response_code,
    #         'response':response,
    #         'data_count':jml_data,
    #         'request_time': request_time,
    #         'response_time': response_time,
    #         'api_type' : 'b2b',
    #     })
    
    def create_log_api(self,htttp_response_code,status,error,error_description,uid,header,response,end_point,ip_address,request_time,response_time,data_count=0):

        self.create({
            'user_id' :uid,
            'header' :header,
            'response' :response,
            'end_point' :end_point,
            'ip_address' :ip_address,
            'request_time' :request_time,
            'response_time' :response_time,
            'htttp_response_code' :htttp_response_code,
            'status' : status,
            'name' :error_description,
            'data_count' :data_count,
            'api_type' : 'b2b'
        })
       
        

    
