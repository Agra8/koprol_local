from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

class eps_purchase_order (models.Model):
    _inherit = 'purchase.order'   

    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True, domain="[('company_id','=',company_id)]") 
    
    def print_quotation(self):
        self.write({'state': "sent"})
        datas = {
             'id': self.id,
             'model': 'purchase.order',
             'data': self.read()[0],
        }
        return self.env.ref('eps_purchase_order.report_print_po_pdf').report_action(self, data=datas)

class eps_snk_po (models.Model):
    _name = "eps.snk.po"
    _description = 'Purchase Order S&K'

    def _get_sequence(self):
        last_code = self.search([('parent_id','=',False)], order='sequence desc', limit=1).sequence
        return last_code+1

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            last_code = self.search([('parent_id','=',self.parent_id.id)], order='sequence desc', limit=1).sequence
            if last_code:
                self.sequence = last_code+1
            else:
                self.sequence = 1
        

    name = fields.Char('Code')
    isi = fields.Text(string="Isi S&K")
    sequence = fields.Integer(string="Urutan S&K", default=_get_sequence)
    # kategori = fields.Selection([
    #     ('A','A. Syarat Umum'),
    #     ('B','B. Barang dan Jasa'),
    #     ('C','C. Pengiriman'),
    #     ('D','D. Pembayaran'),
    #     ('E','E. Komitmen Etika Bisnis'),
    #     ], string='Kategori', default='category', required=True)
    parent_id = fields.Many2one('eps.snk.po', string='Parent')
    child_ids = fields.One2many('eps.snk.po', 'parent_id', string='Childs')

    @api.model
    def create(self,vals):
        if vals.get('parent_id'):
            vals['name'] = self.browse(vals['parent_id']).name+'/'+str(vals['sequence'])
        else:
            vals['name'] = str(vals['sequence'])
        return super(eps_snk_po,self).create(vals) 
    