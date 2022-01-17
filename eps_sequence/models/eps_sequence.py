from odoo import models, fields, api, _

class Sequence(models.Model):
    _inherit = "ir.sequence"

    
    def get_per_doc_code(self,doc_code, prefix):
        seq_name = '{0}/{1}'.format(prefix, doc_code)

        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            vals = {
                'name':seq_name,
                'implementation': 'standard',
                'prefix': prefix,
                'padding':5
            }
            ids = super(Sequence,self).create(vals)
        return ids.next_by_id()
    
    def get_nik_per_branch(self,doc_code):
        seq_name = '{0}'.format('EMP')

        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '%(y)s%(month)s'
            vals = {
                'name':seq_name,
                'implementation':'standard',
                'prefix':prefix,
                'padding':3
            }
            ids = super(Sequence,self).create(vals)
        return ids.next_by_id()

    
    def get_code_md(self,doc_code) :
        ids = self.suspend_security().search([('name','=',doc_code)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = doc_code + prefix
            vals = {
                'name':doc_code,
                'implementation':'no_gap',
                'prefix':prefix,
                'padding':5
            }
            ids = self.create(vals)
        return ids.next_by_id()

    
    def get_code_transaksi_customer(self,dealer,code):
        seq_name = '{0}/{1}'.format(dealer,code)
        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = str(dealer) + str(prefix) + str(code)
            vals = {
                'name':seq_name,
                'implementation':'no_gap',
                'prefix':prefix,
                'padding':4
            }
            ids = self.create(vals)
        return ids.next_by_id()

    
    def get_two_doc_code(self,doc_code1, doc_code2, prefix):
        seq_name = '{0}/{1}/{2}'.format(prefix, doc_code1, doc_code2)
        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            vals = {
                'name':seq_name,
                'implementation': 'standard',
                'prefix': prefix,
                'padding':5
            }
            ids = super(Sequence,self).create(vals)
        return ids.next_by_id()
    
    
    def get_code_transaksi_4(self,code,prefix):
        seq_name = '{0}/{1}'.format(code,prefix)
        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            vals = {
                'name':seq_name,
                'implementation':'no_gap',
                'prefix':prefix,
                'padding':4
            }
            ids = self.create(vals)
        return ids.next_by_id()

    def get_applicant_code(self,code, prefix):
        # code = self.pool.get('wtc.branch').browse(cr, uid, branch_id).code
        seq_name = '{0}/{1}'.format(prefix, code)
        prefix = '/%(y)s%(month)s%(day)s'
        prefix = seq_name + prefix

        ids = self.search([('name','=',seq_name),('prefix','=',prefix)], limit=1)
        if not ids:
            vals = {
                'name':seq_name,
                'implementation': 'standard',
                'prefix': prefix,
                'padding':5
            }
            ids = super(Sequence,self).create(vals)

        return self.get_id(ids.id)
    
    def get_increment_number(self, doc_code, prefix):
        seq_name = '{0}/{1}'.format(prefix, doc_code)

        ids = self.search([('name','=',seq_name)])
        if not ids:
            vals = {
                'name':seq_name,
                'implementation': 'standard',
                'padding':3
            }
            ids = super(Sequence,self).create(vals)
            
        return ids.next_by_id()

    def get_pmk_code(self, prefix):
        seq_name = '{0}/'.format(prefix)

        ids = self.search([('name','=',seq_name)])
        if not ids:
            prefix = '%(day)s/%(month)s/%(y)s-'
            prefix = seq_name + prefix
            vals = {
                'name':seq_name,
                'implementation': 'standard',
                'prefix': prefix,
                'padding':5
            }
            ids = super(Sequence,self).create(vals)
        code =ids.next_by_id().split('-')
        return code[1]+'-'+code[0].replace('PMK/','')
