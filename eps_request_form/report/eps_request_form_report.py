import time
import io
import xlsxwriter
from io import BytesIO
import base64
import tempfile
import os
from odoo import models, fields, api, _
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo.exceptions import Warning
import logging
import re
import pytz
from lxml import etree
import calendar

class EpsRequestFormReport(models.TransientModel):
    _name = "eps.request.form.report"

    @api.model
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    @api.model
    def _get_default_start_date(self):
        return date.today().strftime("%Y-%m-01")

    file = fields.Char('File Name')
    data_x = fields.Binary('file', readonly=True)
    state_x =fields.Selection([('choose', 'choose'),('get', 'get')],default='choose')
    start_date = fields.Date(string='Start Date', default=_get_default_start_date)
    end_date = fields.Date(string='End Date', default=_get_default_date)
    state = fields.Selection(string='State',  selection=[('draft','Draft'),('approved','Approved'),('rejected','Rejected'),('cancel', 'Cancel'),('open', 'Open'),('done', 'Done')])

    # 8: Relation Fields
    branch_ids = fields.Many2many(string='Branch', comodel_name='res.branch')
    def excel_laporan(self):
        return self._download_laporan()
    
    def _download_laporan(self):
        query_where = ""
        if self.branch_ids:
            branch_ids = [id_branch.id for id_branch in self.branch_ids]
            query_where += f" AND rf.branch_id in {str(tuple(branch_ids)).replace(',)', ')')}"
        if self.state:
            query_where += f" AND rfl.state = '{str(self.state)}'"
        query = f"""
                SELECT 
                    cm.name AS company,
                    br.name AS branch,
                    rfl.date AS tanggal,
                    rf.name AS Transaksi_Header,
                    rfl.name AS Transaksi_request,
                    rf.name_pegawai AS nama,
                    tm.name AS team,
                    hr.name AS pic,
                    rfl.keterangan AS keterangan,
                    ms.name AS tipe_request,
                    ss.name AS sistem,
                    rfl.state AS status
                    FROM eps_request_form_line rfl
                    LEFT JOIN eps_request_form rf ON rf.id = rfl.request_form_id
                    LEFT JOIN hr_employee hr ON hr.id = rfl.employee_id
                    LEFT JOIN eps_master_jrf_arf ms ON ms.id = rfl.request_id
                    LEFT JOIN eps_sistem_master ss ON ss.id = rfl.sistem_id
                    LEFT JOIN res_branch br ON br.id = rf.branch_id
                    LEFT JOIN eps_teams_master tm ON tm.id = rfl.teams_id 
                    LEFT JOIN res_company cm ON cm.id = rf.company_id
                    WHERE 1=1
                    {query_where}
                    AND rfl.date >= '{str(self.start_date)}'
                    AND rfl.date <= '{str(self.end_date)}' 
                    ORDER BY rfl.date desc
            """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning("Tidak ada Data")
        
        return self.env['dms.report'].generate_report('Laporan Request Form',ress)
