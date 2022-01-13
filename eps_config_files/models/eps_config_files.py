import time
from datetime import datetime
from odoo import models, fields, api, tools
from odoo.exceptions import Warning,ValidationError
import base64
import os
import tempfile

class EpsConfFiles(models.Model):
    _name = "eps.config.files"
    _description = "Configuration Save Files"
    
    folder_path_local = fields.Char(string='Folder Path Local',required=True)

    @api.model
    def create(self,vals):
        cek = self.search([]) 
        if len(cek) > 0:
            raise Warning('Path sudah di buat !')
        return super(EpsConfFiles,self).create(vals)

    def upload_file(self,file_name,file):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi file')
        local_path = obj.folder_path_local

        link = local_path+'/'+file_name

        try:
            data = base64.decodebytes(bytes(file, 'utf-8'))
        except:
            data = base64.decodebytes(file)
        open(link, 'wb').write(data)

    def get_img(self,file_name):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi file')
        local_path = obj.folder_path_local
        file_get = open(local_path+'/'+file_name, 'rb').read()
        file = base64.encodebytes(file_get)
            # print file
        return file

    def remove_file(self, file_name):
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi file')
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