import base64
import calendar
import io
import logging
import os
import pytz
import re
import string
import time
import tempfile
import xlsxwriter
from io import BytesIO
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from xlsxwriter.utility import xl_rowcol_to_cell
from lxml import etree

class DmsReport(models.TransientModel):
    _name = 'dms.report'
    _description = 'Report Utils'

    
    @api.model
    def _get_default_datetime_plus_7(self): 
        return datetime.now() + timedelta(hours=7)

    name = fields.Char(string='Name')
    report_file = fields.Binary('File', readonly=True)

    
    wbf = {}

    def generate_report(self
        , report_name 
        , data
        , start_date=False
        , end_date=False
        , header=True
        , header_color = '#FFFF00'
        , capitalize=True
        , numbering=True
        , auto_filter=True
        , freeze_panes=True
        , freeze_panes_column=0
        , bottom_remark=True
        ):
        """ Return XLSX Report from the given 'List of Dictionary' data.
            :param report_name: File name of the report before given datetime at the end of it
            :param data: data with 'List of Dictionary' type, the key will be Header and the value will be inserted into each row 
            :param start_date: For report title, if this param is filled, title will generated above header
            :param end_date: For report title, start_date must be filled to show end_date. end date will shown after start_date
            :param header: Enable/Disable header (title) option, header text will generated from data key's, underscores '_' will replaced with space and will capitalize unless all words is uppercase 
            :param header_color: Color of the header, the default will be yellow (#FFFF00)
            :param capitalize: Enable/Disable auto capitalize for header text
            :param numbering: Enable/Disable Numbering. Number will generated at first column. The default will be True
            :param auto_filter: Enable/Disable Auto Filter. 'Auto Filter' will filter first row. The default will be True, however.. this only active when params header is true
            :param freeze_panes: Enable/Disable Freeze Pane. Freeze first column. The default will be True, however.. this only active when params header is true
            :param freeze_panes_column: Freeze column from given integer (starting from 0). The default will be 0, however.. this only active when params header & freeze_panes is true
            :param bottom_remark: Enable/Disable remark Give remark at the bottom of the workbook. The remark contains Downloader name & Download date
            :return: xlsx file of the report generated
        """
        if not data:
            raise Warning("There is no data available.")

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)       
        workbook = self.add_workbook_format(workbook,header_color)
        wbf = self.wbf

        # Give Report name 
        report_name = report_name.replace("/"," ")
        worksheet = workbook.add_worksheet(report_name)
        filename = report_name.lower()+"_"+ str(self._get_default_datetime_plus_7())+'.xlsx'
        
        # Initialize params
        column_size = []
        header_len = len(list(data[0].keys()))
        header_row = 0
        number = 1
        row = 0
        col = 0

        # Handle title
        if start_date:
            # Change header row
            header_row = 3

            # Setup title
            worksheet.merge_range(row,col,row,header_len, report_name, wbf['title_doc'])
            time_title = str(start_date)
            if end_date:
                time_title += ' - '+str(end_date)
            row += 1
            worksheet.merge_range(row,col,row,header_len, time_title, wbf['title_doc'])

            row += 2

        for line in data:
            col = 0
            # Handle header (First data)
            if header and number == 1:
                
                # Give column number
                if numbering:
                    worksheet.write(row, col, "No", wbf['header'])
                    column_size.append(2)
                    col += 1
                
                # Loop key for Header/Title
                for key in line:
                    # Wirte Header Title with key from dictionary
                    formated_header_string = key.replace('_',' ')
                    # IF capitalize params is true and not all word is uppercase, capitalize words
                    if capitalize and not formated_header_string.isupper():
                        formated_header_string = formated_header_string.capitalize()

                    worksheet.write(row, col, formated_header_string, wbf['header'])
                    
                    # Write initial column size
                    column_size.append(len(str(formated_header_string)))
                    col+=1
                row +=1
                col = 0

            # Give column number
            if numbering:
                worksheet.write(row, col, number, wbf['content'])
                col += 1

            # Write Content
            for key in line:
                # Define Cell format
                cell_format = 'content'
                if isinstance(line[key], float):
                    cell_format = 'content_float'
                worksheet.write(row, col, line[key], wbf[cell_format])

                # Change column size if content bigger than previous stored size
                current_column_index = list(line.keys()).index(key) + int(numbering)
                if column_size[current_column_index] < len(str(line[key])):
                    column_size[current_column_index] = (len(str(line[key])))

                col+=1
            
            row +=1
            number +=1
        
        # set column width
        for i in range(0, len(column_size)):
            worksheet.set_column(i, i, column_size[i]+2)

        # set auto_filter (only if worksheet have header)
        if header and auto_filter:
            worksheet.autofilter(header_row, 0, row-1, col-1)

        # freeze panes (only if worksheet have header)
        if header and freeze_panes:
            # Handle freeze_panes_column params, and check format 
            to_freeze_column = 0
            if isinstance(freeze_panes_column,int):
                to_freeze_column = freeze_panes_column

            worksheet.freeze_panes(header_row+1, to_freeze_column)
        
        # Set bottom remark
        if bottom_remark:
            worksheet.merge_range('A%s:D%s'%(row+2,row+2), '%s - %s' % (self.sudo().env.user.name, str(self._get_default_datetime_plus_7())) , wbf['footer']) 
            
        workbook.close()
        out=base64.encodebytes(fp.getvalue())
        report = self.sudo().create({
            'report_file' : out,
            'name' : filename,
        })
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/dms.report/%s/report_file/%s?download=true' % (report.id, filename)
        }  
            
        
    
    def add_workbook_format(self, workbook, header_color):
        
        self.wbf['title_doc'] = workbook.add_format({'bold': 1,'align': 'left'})
        self.wbf['title_doc'].set_font_size(12)

        self.wbf['footer'] = workbook.add_format({'align':'left'})

        self.wbf['header'] = workbook.add_format({'bg_color':header_color,'bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header'].set_top(2)
        self.wbf['header'].set_bottom()
        self.wbf['header'].set_left()
        self.wbf['header'].set_right()
        self.wbf['header'].set_font_size(11)
        self.wbf['header'].set_align('vcenter')

        self.wbf['content'] = workbook.add_format({'align': 'left','font_color': '#000000'})
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_top()
        self.wbf['content'].set_bottom()
        self.wbf['content'].set_font_size(10)                

        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()
        self.wbf['content_float'].set_top()
        self.wbf['content_float'].set_bottom()
        self.wbf['content_float'].set_font_size(10)                
        
        return workbook   
    