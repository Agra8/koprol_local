import time
import string
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta

class EpsPrintPo(models.AbstractModel):
    _name = 'report.eps_purchase_order.print_po_pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        sp_obj = self.env['purchase.order'].sudo().browse(data['id'])
        snk = self.env['eps.snk.po'].sudo().search([('parent_id','=',False)])
        alp_up_string = string.ascii_uppercase
        alp_up = list(alp_up_string)
        alp_low_string = string.ascii_lowercase
        alp_low = list(alp_low_string)
        return {
                'sp_obj': sp_obj,
                'snk': snk,
                'alp_up':alp_up,
                'alp_low':alp_low
            }