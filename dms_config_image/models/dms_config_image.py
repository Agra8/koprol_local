import time
from datetime import datetime
from odoo import models, fields, api, tools
from odoo.exceptions import Warning,ValidationError
import base64
import pysftp
import os
import tempfile
import platform
import subprocess
import sys
import urllib

class DmsConfImage(models.Model):
    _name = "dms.conf.image"
    _description = "Configuration Save Image"
    
    folder_path_local = fields.Char(string='Folder Path Local',required=True)

    @api.model
    def create(self,vals):
        cek = self.search([]) 
        if len(cek) > 0:
            raise Warning('Path sudah di buat !')
        return super(DmsConfImage,self).create(vals)

    def upload_file(self,file_name,file):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi image')
        local_path = obj.folder_path_local

        link = f'{local_path}/{file_name}'

        # Convert Image
        file_split = file_name.split('.')
        file_ext = file_split[-1]
        if file_ext in ('jpg','jpeg','png','gif','JPG','JPEG','PNG','GIF'):
            try:
                file = tools.image_resize_image_big(file,size=(2000,None), filetype=None, avoid_if_small=True)
            except:
                file = file
        try:
            data = base64.decodebytes(bytes(file, 'utf-8'))
        except:
            data = base64.decodebytes(file)
        open(link, 'wb').write(data)


    def get_img(self,file_name):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi image')
        local_path = obj.folder_path_local
        full_path = f'{local_path}/{file_name}'
        if os.path.exists(full_path):
            file_get = open(full_path, 'rb').read()
            file = base64.encodebytes(file_get)
            return file
        else:
            return False

        
    def remove_file(self, file_name):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi image')
        local_path = obj.folder_path_local
        link = local_path + '/' + file_name
        # If file exists, delete it
        if os.path.isfile(link):
            os.remove(link)
        return True

    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        for record in self :
            tit = "%s" % (record.folder_path_local)
            res.append((record.id, tit))
        return res

    def cek_size(self,file_name):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi image')
        local_path = obj.folder_path_local
        file_size = os.path.getsize(local_path+"/"+file_name)
        return file_size

    def compress_pdf(self, file_name, power=3, need_compression_size = 100000):
        """Function to compress PDF via Ghostscript command line interface"""
        """
            INSTALLATION
                
                On Linux: apt install ghostscript
                On MacOSX: brew install ghostscript 
                On Windows: install binaries via [official website] (https://www.ghostscript.com/)

                calling ghoscript on windows should be like this:

                    subprocess.call(['C:/Program Files/gs/gs9.54.0/bin/gswin64.exe', '-sDEVICE=pdfwrite', '-dCom
                
                to make this script run for both windows and linux. If you are using windows device, 
                please : Put 'GS /bin folder' in path on your System Environment Variable. the default will be C:/Program Files/gs/gs9.54.0/bin/
                    
        """
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi image')
        local_path = obj.folder_path_local
        file_path = f'{local_path}/{file_name}'

        # Select the compression Power 
        # 0 is the lowest (May not shrinking the document)
        # 4 is the greatest (May reduce image quality so bad)
        quality = {
            0: '/default',
            1: '/prepress',
            2: '/printer',
            3: '/ebook',
            4: '/screen'
        }

        # Check size of the file, we do compression if the file larger than 1 mb
        file_size = self.cek_size(file_name=file_name)
        if file_size > need_compression_size:
            # Set input file, so output file will remain the origin name
            input_file_path = file_path.replace(".pdf", "_COMPRESS_BACKUP.pdf")
            os.rename(file_path, input_file_path)

            # GhostScript Calling is different on windows
            gs_name = 'gs'
            if platform.system() == 'Windows':
                gs_name = 'gswin64.exe'

            # Call GhostScript with subprocess
            subprocess.call([gs_name, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.7',
                             '-dPDFSETTINGS={}'.format(quality[power]),
                             '-dNOPAUSE', '-dQUIET', '-dBATCH',
                             '-sOutputFile={}'.format(file_path),
                             input_file_path]
                            )
            
            # TODO: Turn this back on, if we think it's safe enaugh  (21 June 2021)
            # Remove original(Backup) file
            # os.remove(input_file_path)

            # If the compression failed with current power, up the power and redo compression
            final_file_size = self.cek_size(file_name=file_name)
            ratio = 1 - (final_file_size / file_size)
            
            # We use ratio, normal ratio for compression is 0.3 - 0.7
            if ratio < 0.1 and power != 4:
                self.compress_pdf(file_name=file_name, power=power+1)