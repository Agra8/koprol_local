import itertools
from lxml import etree
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.osv import osv
        
class eps_res_partner (models.Model):
    _inherit = 'res.partner'
    
    # driver=fields.Boolean('Driver')
    # operator=fields.Boolean('Operator')