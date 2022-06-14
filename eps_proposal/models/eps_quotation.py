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
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, domain="[('supplier_rank','=',1),('state','=','approved')]")
    validity_date = fields.Date('Valid Until', required=True)
    file_document = fields.Binary(string="File Document")
    filename_document = fields.Char(string="File Document")
    filename_upload_document = fields.Char(string="Filename upload Document")
    file_document_show = fields.Binary(string="File Document", compute='_compute_file_document')
    # state = fields.Selection(selection=[('draft','Quotation'),('negotiation','Negotiation'),('final_tender','Final Tender')],default='draft',  string='State',  help='')
    state = fields.Selection([
                            ('invalid','Invalid'),
                            ('valid','Valid'),
                            ('proposed','Proposed'),
                            ('won','Won')], string='Status',  help='', default='valid')
    quotation_line_ids = fields.One2many('eps.quotation.line', 'quotation_id', string='Quotation Detail')
    amount_untaxed = fields.Float(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Float(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives')
    company_id = fields.Many2one('res.company', string='Company', related='initiatives_id.company_id', store=True, tracking=True)
    branch_id = fields.Many2one('res.branch', domain="[('company_id','=',company_id)]", string='Branch', related='initiatives_id.branch_id', store=True, tracking=True)
    divisi_id = fields.Many2one('eps.divisi', string='Divisi', related='initiatives_id.divisi_id', store=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', related='initiatives_id.department_id', store=True, tracking=True)
    revision = fields.Integer('Rev. No')
    quotation_amount = fields.Float('Quotation Amount')
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','eps.quotation')], copy=False)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    initiatives_state = fields.Selection(related='initiatives_id.state', store=True, string='Initiatives Status')

    @api.constrains('supplier_id')
    def _check_supplier(self):
        for record in self:
            if not record.supplier_id.vendor_registration_doc:
                check_record = self.env['eps.initiatives.line'].search([('supplier_id','=',record.supplier_id.id),
                                                                        ('initiatives_id','!=',record.initiatives_id.id),
                                                                        ('initiatives_id.state','=','done')
                                                                    ])
                if check_record:
                    raise ValidationError('Vendor %s sudah pernah dipakai untuk transaksi one time purchase, jika ingin menggunakan vendor ini silahkan lengkapi dokumen persyaratan untuk menjadi recurring vendor')

    @api.constrains('quotation_amount')
    def _check_quotation_amount(self):
        for record in self:
            if record.quotation_amount<=0:
                raise ValidationError('Quotation amount harus >0 !')

    @api.constrains('amount_total')
    def _check_amount_total(self):
        for record in self:
            if record.initiatives_state=='approved' and record.quotation_amount!=record.amount_total:
                raise ValidationError('Quotation amount %s tidak sama dengan Total quotation line!' % (record.name))

    @api.constrains('initiatives_id')
    def _check_initiatives(self):
        for record in self:
            if not record.initiatives_id:
                raise ValidationError('There is no initiatives selected for this quotation!')

    @api.depends('filename_upload_document')
    def _compute_file_document(self):
        for rec in self:
            if rec.filename_upload_document:
                image_document = rec.env['eps.config.files'].sudo().get_img(rec.filename_upload_document)
                rec.file_document_show = image_document
            else : 
                rec.file_document_show = False

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
        for rec in old_docs.filtered(lambda x:x.state in ('valid','proposed')):
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


    def action_set_won(self):
        to_initiative = []
        for record in self:
            if not record.quotation_line_ids:
                raise ValidationError('Detail quotation masih kosong!')
            for line in record.quotation_line_ids:
                if not line.product_id:
                    product = line.create_product_from_quotation()
                    line.write({'product_id': product.id})
                to_initiative.append([0, False, line._prepare_initiatives_line()])

            if to_initiative and record.initiatives_id:
                record.initiatives_id.write({'initiatives_line_ids': to_initiative})
            record.write({'state':'won'})
        # return {
        #           'type': 'ir.actions.client',
        #           'tag': 'reload',
        #           'params': {'wait': True}
        #     }

    def action_set_proposed(self):
        for record in self:
            record.write({'state':'proposed'})

    def action_request_approval(self):
        self.env['eps.matrix.approval.line'].request_by_value(self, self.quotation_amount)
        self.write({'state':'waiting_for_approval', 'approval_state':'rf'})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))

    def open_record(self):
        # first you need to get the id of your record
        # you didn't specify what you want to edit exactly
        # then if you have more than one form view then specify the form id
        form_id = self.env.ref('eps_proposal.eps_quotation_form_view')

        # then open the form
        return {
                'type': 'ir.actions.act_window',
                'name': 'Quotation',
                'res_model': 'eps.quotation',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': form_id.id,
                'context': {},  
                # if you want to open the form in edit mode direclty            
                # 'flags': {'initial_mode': 'edit'},
                'target': 'current',
            }


class QuotationLines(models.Model):
    _name = "eps.quotation.line"
    _description = 'Quotation Lines'

    quotation_id = fields.Many2one('eps.quotation', string='Quotation', ondelete='cascade')
    categ_id = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Item')
    name = fields.Char(string='Name', required=True)
    quantity = fields.Float('Quantity', default=1)
    price_unit = fields.Float('Unit Price')
    discount = fields.Float('Discount')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Float(compute='_compute_amount', string='Total (Tax Included)', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)
    product_type = fields.Selection([('consu','Consumable'),('service','Service')], string='Product Type')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.name = self.product_id.name
            self.categ_id = self.product_id.categ_id.id
            self.product_type = self.product_id.type

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

    def create_product_from_quotation(self):
        """
        if there is no product in line, then create a new one from here
        """
        product = False
        for line in self:
            product_vals = {
            'name': line.name,
            'purchase_ok': True,
            'categ_id': line.categ_id.id,
            'type': line.product_type,
            }
            product = self.env['product.product'].create(product_vals)
        return product


    def _prepare_initiatives_line(self):
        data = {}
        for line in self:
            data ={
            'branch_id' : line.quotation_id.branch_id.id,
            'initiatives_id' : line.quotation_id.initiatives_id.id,
            'supplier_id' : line.quotation_id.supplier_id.id,
            'product_id' : line.product_id.id,
            'quantity' : line.quantity,
            'price_unit' : line.price_unit,
            'discount' : line.discount,
            'tax_id' : [(6,0,line.tax_id.ids)],
            'quotation_line_id': line.id
            }
        return data

