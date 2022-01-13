from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from docxtpl import DocxTemplate, R, InlineImage
import subprocess
import base64
import os
import platform
from odoo.tools import config
from docx2pdf import convert
from datetime import datetime
import qrcode
from docx.shared import Mm
from werkzeug.urls import url_encode
from datetime import datetime, timedelta
import pytz
from pytz import timezone

class Initiatives(models.Model):
    _name = "eps.initiatives"
    _description = 'Initiatives'
    _inherit = ['mail.thread']

    @api.depends('initiatives_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.initiatives_line_ids:
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

    name = fields.Char('Name', required=True, default='/')
    date = fields.Date('Date', required=True, tracking=True, default=_get_default_date)
    company_id = fields.Many2one('res.company', string='Company', required=True, tracking=True)
    branch_id = fields.Many2one('res.branch', domain="[('company_id','=',company_id)]", string='Branch', required=True, tracking=True)
    divisi_id = fields.Many2one('eps.divisi', string='Divisi', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', domain="[('company_id','=',company_id)]", string='Department', required=True, tracking=True)
    proposal_id = fields.Many2one('eps.proposal', required=True, string='Proposal', domain="[('company_id','=',company_id),('branch_id','=',branch_id),('divisi_id','=',divisi_id),('department_id','=',department_id),('state','=','approved')]", tracking=True)
    proposal_line_id = fields.Many2one('eps.proposal.line', domain="[('proposal_id','=',proposal_id)]", string='Category', tracking=True, required=True)
    reserved_amount = fields.Float('Reserved Amount')
    remarks = fields.Text('Remarks')
    initiatives_line_ids = fields.One2many('eps.initiatives.line', 'initiatives_id', string='Detail Initiatives')
    type = fields.Selection([('Request for Quotations','Request for Quotations'),('Tender','Tender'),('Kontrak Payung','Kontrak Payung')], string='Type', required=True)
    state = fields.Selection(selection=[('draft','Draft'),('review_ga','Review GA'),('waiting_for_approval','Waiting for Approval'),('approved','Approved'),('done','Done')], default='draft',  string='State',  help='', tracking=True)
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','eps.initiatives')], copy=False)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, string='Currency', readonly=True)
    quotation_line_ids = fields.One2many('eps.quotation', 'initiatives_id', string='Detail Quotations')

    def validity_check(self):
        for record in self:
            if not record.initiatives_line_ids:
                raise ValidationError('Detail Initiatives masih kosong!')

    def action_request_approval(self):
        self.validity_check()
        self.env['eps.matrix.approval.line'].request_by_value(self, self.amount_total)
        self.write({'state':'waiting_for_approval', 'approval_state':'rf'})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))

    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].get_per_branch(vals['branch_id'], 'IN')
        vals['date'] = self._get_default_date()
        ids = super(Initiatives,self).create(vals)    
        return ids

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Tidak bisa hapus transaksi dalam status selain draft!'))
        return super(Initiatives, self).unlink()

    @api.onchange('company_id','branch_id','divisi_id','department_id')
    def _onchange_company_branch(self):
        if self.company_id:
            if self.branch_id:
                if self.branch_id.company_id.id!=self.company_id.id:
                    self.branch_id = False
                    self.divisi_id = False
                    self.department_id = False
                    self.proposal_id = False
                    self.proposal_line_id = False
            if self.divisi_id and self.department_id and self.branch_id:
                if self.divisi_id.id!=self.proposal_id.divisi_id.id or self.department_id.id!=self.proposal_id.department_id.id:
                    self.proposal_id = False
                    self.proposal_line_id = False
        
        if self.branch_id:
            if self.divisi_id and self.department_id and self.company_id:
                if self.divisi_id.id!=self.proposal_id.divisi_id.id or self.department_id.id!=self.proposal_id.department_id.id:
                    self.proposal_id = False
                    self.proposal_line_id = False
        
        if self.divisi_id:
            if self.branch_id and self.department_id and self.company_id:
                if self.divisi_id.id!=self.proposal_id.divisi_id.id or self.department_id.id!=self.proposal_id.department_id.id:
                    self.proposal_id = False
                    self.proposal_line_id = False

        if self.department_id:
            if self.branch_id and self.divisi_id and self.company_id:
                if self.divisi_id.id!=self.proposal_id.divisi_id.id or self.department_id.id!=self.proposal_id.department_id.id:
                    self.proposal_id = False
                    self.proposal_line_id = False

class InitiativesLines(models.Model):
    _name = "eps.initiatives.line"
    _description = 'Initiatives Lines'

    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives')
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, domain="[('supplier_rank','=',1)]")
    product_id = fields.Many2one('product.product', string='Item', required=True)
    quantity = fields.Float('Quantity')
    price_unit = fields.Float('Unit Price')
    discount = fields.Float('Discount')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total (Tax Included)', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)
    company_id = fields.Many2one('res.company', related='initiatives_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related='initiatives_id.company_id.currency_id', store=True, string='Currency', readonly=True)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the Initiatives line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.initiatives_id.company_id.currency_id, line.quantity, product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('supplier_id','product_id')
    def _onchange_supplier_product(self):
        if self.supplier_id and self.product_id:
            quotation = self.env['eps.quotation.line'].search([
                ('product_id','=',self.product_id.id),
                ('quotation_id.supplier_id','=',self.supplier_id.id),
                ('quotation_id.validity_date','>=',self.initiatives_id.date.strftime('%Y-%m-%d')),
                ('quotation_id.stage','=','valid')
                ],limit=1,order='id desc')
            
            if quotation:
                self.price_unit=quotation.price_unit
                self.discount=quotation.discount
                self.tax_id=quotation.tax_id.ids
            else:
                self.price_unit=False
                self.discount=False
                self.tax_id=False
            



