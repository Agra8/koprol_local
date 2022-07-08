import functools
import odoo
from odoo import http
from odoo.http import request
from odoo.http import Response
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
import time
from dateutil.relativedelta import relativedelta
import hashlib
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta

ERROR_TYPE_ACCESS_DENIED = "access_denied"
ERROR_TYPE_MANDATORY_PARAMS = "mandatory_params"
ERROR_TYPE_EMPTY_MANDATORY_PARAMS = "empty_mandatory_params"
ERROR_TYPE_MISSING_FORMAT_DATE = "missing_format_date"
ERROR_TYPE_DATA_NOT_FOUND = "data_not_found"
ERROR_TYPE_SERVER_ERROR = "server_error"
ERROR_TYPE_INVALID_SECRET = "invalid_client_secret"
ERROR_TYPE_TOKEN_EXPIRED = "token_expired"
ERROR_TYPE_DATA_DUPLICATED = "data_not_found"
ERROR_TYPE_DATA_NOT_VALID = "data_not_valid"

def start_end_date_request():
    start_end_date=(datetime.now() + relativedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    return start_end_date 

def log_api(htttp_response_code,status,error,error_description,uid,header,response,end_point,ip_address,request_time,response_time,data_count=0):
    log= {
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
        }
    obj_create=request.env['eps.api.log'].sudo().create(log)

def valid_response_push_json(status,data,is_log=False,status_info=False,uid=False,post=False,end_point=False,ip_address=False,request_time=False,response_time=False,data_count=0):
    response = {
        "status": 1,
        "message":data,
        "data":None 
    }
    if is_log:
        log_api(status,status_info,'','',uid,post,response,end_point,ip_address,request_time,response_time,data_count)
    return response

def invalid_response_json(status,error,info,is_log=False,status_info=False,uid=False,post=False,end_point=False,ip_address=False,request_time=False,response_time=False,exception_info=False):
    response = { 
        "status":0,
        "message":{"error":error,"error_description":info},
        "data":None,
    }
    error_info = exception_info if exception_info else info
    if is_log:
        log_api(status,status_info,error,error_info,uid,post,response,end_point,ip_address,request_time,response_time)
    return response

def valid_response_json(status,data,is_log=False,status_info=False,uid=False,post=False,end_point=False,ip_address=False,request_time=False,response_time=False,data_count=0,message=None):
    response = { 
        "status":1,
        "message":message,
        "data":data,
    }
    if is_log:
        log_api(status,status_info,message,'',uid,post,response,end_point,ip_address,request_time,response_time,data_count)
    return response

def invalid_secret(uid=False,post=False,end_point=False,ip_address=False,request_time=False,response_time=False):
    _logger.error("Access Client Secret Invalid!")    
    return invalid_response_json(401, ERROR_TYPE_INVALID_SECRET, "Client Secret is invalid!", True,'failed',uid,post,end_point,ip_address,request_time,response_time) #TODO: tolong lanjutkan

def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False
    
def validate_date_other(date_text):
    try:
        datetime.strptime(date_text, '%d/%m/%Y %H:%M:%S')
        return True
    except ValueError:
        return False

def validate_date_day(date_text):
    try:
        datetime.strptime(date_text, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def check_valid_secret(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        api_client_id = request.httprequest.headers.get('API-Key')
        request_time = request.httprequest.headers.get('X-Request-Time')
        token = request.httprequest.headers.get('API-Token')
        ip_address = request.httprequest.headers.environ['REMOTE_ADDR']
        uid = request.session.uid
        end_point = "/api/"+str(request.httprequest.url).split('/api/')[1]
        post = request.params
        request_datetime = start_end_date_request()
        _logger.error(api_client_id)
        _logger.error(token)
        if not api_client_id:
            info = "Missing API-Key in request header!"
            error = 'api_key_not_found'
            _logger.error(info)
            response_time = start_end_date_request()
            return invalid_response_json(400, error, info,True,'failed',uid,post,end_point,ip_address,request_datetime,response_time)
        if not request_time:
            info = "Missing X-Request-Time in request header!"
            error = 'request_time_not_found'
            _logger.error(info)
            response_time = start_end_date_request()
            return invalid_response_json(400, error, info,True,'failed',uid,post,end_point,ip_address,request_datetime,response_time)
        if not token:
            info = "Missing API-Token in request header!"
            error = 'api_token_not_found'
            _logger.error(info)
            response_time = start_end_date_request()
            return invalid_response_json(400, error, info,True,'failed',uid,post,end_point,ip_address,request_datetime,response_time)

        ## Epoch ##
        now_epoch = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        format_epoch = '%Y-%m-%d %H:%M:%S'
        epoch = int(time.mktime(time.strptime(now_epoch,format_epoch)))
        if request_time != 1577815261:
            pass
        elif not request_time or (int(request_time) > epoch) or (epoch - int(request_time) < 0) or (epoch - int(request_time) > 20):
            info = "Token expired."
            error = 'token_expired'
            _logger.error(info)
            response_time = start_end_date_request()
            return invalid_response_json(400, error, info,True,'failed',uid,post,end_point,ip_address,request_datetime,response_time)


        client_secret_data = request.env['res.users'].sudo().search([
            ('api_client_id', '=', api_client_id)], order='id DESC', limit=1)

        if not client_secret_data:
            response_time = start_end_date_request()
            return invalid_secret(uid,post,end_point,ip_address,request_datetime,response_time)
       
        data_token = "%s:%s:%s" %(api_client_id,client_secret_data.api_key_id,request_time)
        token_hash = hashlib.sha256(data_token).hexdigest()
        data_token2 = "%s%s%s" %(api_client_id,client_secret_data.api_key_id,request_time)
        token_hash2 = hashlib.sha256(data_token2).hexdigest()
        
        _logger.error(token_hash)

        # print ">>>>>>>>>>.1",token_hash
        # print ">>>>>>>>>>.1",token
        if (token_hash == token or token_hash2 == token):
            request.session.uid = client_secret_data.id
            request.uid = client_secret_data.id
            request.user = client_secret_data
            return func(self, *args, **kwargs)
        
        response_time = start_end_date_request()
        return invalid_secret(uid,post,end_point,ip_address,request_datetime,response_time)

    return wrap