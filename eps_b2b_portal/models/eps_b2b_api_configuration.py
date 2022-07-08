from datetime import datetime
from openerp import models, fields, api
import requests
import json

class B2bApiConfiguration(models.Model):
    _name = "eps.b2b.api.configuration"

    name = fields.Char(string="Name")
    api_type = fields.Selection([('general','General'),('tops','TOPS')],string="API Type",index=True)
    base_url = fields.Char('Base URL')
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client Secret')
    api_key = fields.Char('API Key')
    api_secret = fields.Char('API Secret')
    verify = fields.Boolean('Verify')
    
    username = fields.Char('Username')
    password = fields.Char('Password')
    database = fields.Char('Database')

    
    def post(self, name, url, body, headers, type='outgoing', verify=True, log=True):
        request_time = datetime.now()
        response = requests.post(url=url, json=body, headers=headers, verify=verify)
        response_time = datetime.now()
        data_count = 0
        if response.status_code == 200:
            content = json.loads(response.content)
            data_count = len(content.get('data',[]) if content.get('data') else [])
        if log:
            # TODO sementara request_time & response_time DGI dulu
            self.env['teds.b2b.api.log'].suspend_security().create_log_api(name, type, url, 'post', {'headers': headers, 'body': body}, response.status_code, response.content, data_count, request_time, response_time)
        return response


    
    def check_config(self,api_type):
        config = self.suspend_security().search([('api_type','=',api_type)],limit=1)
        return config
    
    
    def create_log_error_dgi(self,name,url,request_type,error,origin):
        print (">>>>>>>")


    

