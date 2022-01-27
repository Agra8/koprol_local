from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import subprocess
import base64
import os
import platform
from odoo.tools import config
from datetime import datetime
import qrcode
from werkzeug.urls import url_encode
import pytz
from pytz import timezone

class Quotation(models.Model):
    _name = "eps.quotation"
    _description = 'Quotation'
    _inherit = ['mail.thread']

    @api.depends('quotation_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.quotation_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def _get_default_date(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    name = fields.Char(string='Quotation Name', required=True, default='/')
    ref = fields.Char(string='Reference')
    date = fields.Date(string='Date', required=True, default=_get_default_date)
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, domain="[('supplier_rank','=',1)]")
    validity_date = fields.Date('Valid Until', required=True)
    file_document = fields.Binary(string="File Document")
    filename_document = fields.Char(string="File Document")
    filename_upload_document = fields.Char(string="Filename upload Document")
    file_document_show = fields.Binary(string="File Document", compute='_compute_file_document')
    # state = fields.Selection(selection=[('draft','Quotation'),('negotiation','Negotiation'),('final_tender','Final Tender')],default='draft',  string='State',  help='')
    state = fields.Selection(selection=[('invalid','Invalid'),('valid','Valid'),('final','Final')], string='Status',  help='', default='valid')
    quotation_line_ids = fields.One2many('eps.quotation.line', 'quotation_id', string='Quotation Detail')
    amount_untaxed = fields.Float(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Float(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives')
    revision = fields.Integer('Rev. No')

    @api.depends('filename_upload_document')
    def _compute_file_document(self):
        if self.filename_upload_document:
            image_document = self.env['eps.config.files'].sudo().get_img(self.filename_upload_document)
            self.file_document_show = image_document
        else : 
            self.file_document_show = False

    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].get_per_form('QUO')
        vals['date'] = self._get_default_date()
        if vals.get('file_document'):
            file_document = vals['file_document']
            vals['file_document'] = False
        else:
            file_document = False

        old_docs = self.search([('initiatives_id','=',vals['initiatives_id']),('supplier_id','=',vals['supplier_id'])])
        for rec in old_docs:
            rec.write({'state':'invalid'})
        vals['revision'] = len(old_docs)+1
            
        ids = super(Quotation,self).create(vals)    
        if file_document:
            tmp_kk = vals['filename_document'].split('.')
            ext = tmp_kk[len(tmp_kk) - 1]
            if ext not in ('pdf', 'PDF'):
                raise Warning('Maaf, format file harus pdf')
            filename_document = str('eps_quotation_')+str(ids.id)+'.'+ext
            self.env['eps.config.files'].sudo().upload_file(filename_document, file_document)
            ids.filename_upload_document=filename_document

        
        return ids

    def write(self,vals):
        if vals.get('file_document'):
            file_document = vals['file_document']
            vals['file_document'] = False
            tmp_kk = vals['filename_document'].split('.')
            ext = tmp_kk[len(tmp_kk) - 1]
            if ext not in ('pdf', 'PDF'):
                raise Warning('Maaf, format file harus pdf')
            filename_document_up = str('eps_proposal_')+str(self.id)+'.'+ext
            self.env['eps.config.files'].upload_file(filename_document_up, file_document)
            vals['filename_upload_document']=filename_document_up
        return super(Quotation,self).write(vals)

    def unlink(self):
        for record in self:
            if record.state != 'valid':
                raise UserError(_('Tidak bisa hapus transaksi dalam status selain valid!'))
        return super(Quotation, self).unlink()

    def action_set_final(self):
        for record in self:
            if not record.quotation_line_ids:
                raise ValidationError('Detail quotation masih kosong!')
            for line in record.quotation_line_ids:
                if not line.product_id:
                    product_vals = {
                    'name': line.name,
                    'purchase_ok': True,
                    'categ_id': line.categ_id.id,
                    'type': 'consu',
                    }
                    product = self.env['product.product'].create(product_vals)
                    line.write({'product_id': product.id})
            record.write({'stage':'valid','state':'final_tender'})

    def action_set_invalid(self):
        for record in self:
            record.write({'stage':'invalid'})

    def action_negotiation(self):
        for record in self:
            if not record.quotation_line_ids:
                raise ValidationError('Detail quotation masih kosong!')
            record.write({'state':'negotiation'})

class QuotationLines(models.Model):
    _name = "eps.quotation.line"
    _description = 'Quotation Lines'

    quotation_id = fields.Many2one('eps.quotation', string='Quotation')
    categ_id = fields.Many2one('product.category', string='Category')
    product_id = fields.Many2one('product.product', string='Item')
    name = fields.Char(string='Name', required=True)
    quantity = fields.Float('Quantity', default=1)
    price_unit = fields.Float('Unit Price')
    discount = fields.Float('Discount')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Float(compute='_compute_amount', string='Total (Tax Included)', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the Initiatives line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, self.env['res.users'].browse(self._uid).company_id.currency_id, line.quantity, product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })