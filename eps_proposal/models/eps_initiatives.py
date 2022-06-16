from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,Warning
import subprocess
import base64
import os
import platform
from odoo.tools import config
from datetime import datetime
import qrcode
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

    def _compute_tender(self):
        for record in self:
            tender_count = 0
            if record.type in ('Kontrak Payung','Tender'):
                tender_count = len(self.env['eps.tender'].search([('initiatives_id','=',record.id)]))
            record.tender_count = tender_count

    def _compute_purchase(self):
        for record in self:
            purchase_count = 0
            purchase_count = len(self.env['purchase.order'].search([('initiatives_id','=',record.id)]))
            record.purchase_count = purchase_count


    name = fields.Char('Name', required=True, default='/')
    date = fields.Date('Date', required=True, tracking=True, default=_get_default_date)
    company_id = fields.Many2one('res.company', string='Company', required=True, tracking=True)
    branch_id = fields.Many2one('res.branch', domain="[('company_id','=',company_id)]", string='Branch', required=True, tracking=True)
    divisi_id = fields.Many2one('eps.divisi', string='Divisi', required=True, tracking=True, domain="[('company_id','=',company_id)]")
    department_id = fields.Many2one('hr.department', domain="[('company_id','=',company_id)]", string='Department', required=True, tracking=True)
    proposal_id = fields.Many2one('eps.proposal', required=True, string='Proposal', domain="[('company_id','=',company_id),('branch_id','=',branch_id),('divisi_id','=',divisi_id),('department_id','=',department_id),('state','=','approved')]", tracking=True)
    proposal_line_id = fields.Many2one('eps.proposal.line', domain="[('proposal_id','=',proposal_id)]", string='Category', tracking=True, required=True)
    remarks = fields.Text('Remarks')
    initiatives_line_ids = fields.One2many('eps.initiatives.line', 'initiatives_id', string='Detail Initiatives')
    type = fields.Selection([('One Time Purchase','One Time Purchase'),('Kontrak Payung','Kontrak Payung'),('Tender','Tender')], string='Type', required=True, default='One Time Purchase')
    state = fields.Selection(selection=[('draft','Draft'),('waiting_for_tender','Waiting for Tender'),('waiting_for_approval','Waiting for Approval'),('approved','Approved'),('done','Done')], default='draft',  string='State',  help='', tracking=True)
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','eps.initiatives')], copy=False)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, string='Currency', readonly=True)
    quotation_line_ids = fields.One2many('eps.quotation', 'initiatives_id', string='Detail Quotations')
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')
    tender_count = fields.Integer(compute="_compute_tender", string='Tender Count', default=0)
    purchase_count = fields.Integer(compute="_compute_purchase", string='Tender Count', default=0)
    proposal_amount = fields.Float(related='proposal_line_id.price', store=True, string='Proposal Amount')
    reserved_amount = fields.Float(related='proposal_line_id.reserved_amount', store=True,string='Reserved Amount')

    @api.onchange('proposal_line_id')
    def _onchange_proposal_line(self):
        if self.proposal_line_id:
            data_product = []
            for line in self.proposal_id.proposal_product_line_ids.filtered(lambda x:x.product_id.categ_id.proposal_categ_id == self.proposal_line_id.categ_id):
                data_product.append([0,False,{
                    'branch_id' : line.branch_id.id,
                    'supplier_id' : line.supplier_id.id,
                    'product_id' : line.product_id.id,
                    'price_unit' : line.price_unit,
                    'quantity' : line.quantity,
                    'tax_id' : [(6,0,line.product_id.supplier_taxes_id.ids)]
                    }])
            if data_product:
                self.initiatives_line_ids = False
                self.initiatives_line_ids = data_product

    def validity_check(self):
        for record in self:
            # if not record.initiatives_line_ids:
            #     raise ValidationError('Detail Initiatives masih kosong!')
            if not record.quotation_line_ids.filtered(lambda x:x.state=='proposed') and not record.initiatives_line_ids:
                raise ValidationError('Tidak ada Quotation yang dipropose!')

    def action_request_approval(self):
        self.validity_check()
        amount_approval = sum(q.quotation_amount for q in self.quotation_line_ids.filtered(lambda x:x.state=='proposed'))
        koprol_setting = self.env['eps.koprol.setting'].sudo().search([])
        if not koprol_setting:
            raise ValidationError('Konfigurasi registrasi vendor belum lengkap, silahkan setting terlebih dahulu')
        self.env['eps.matrix.approval.line'].with_context(company_id=koprol_setting.default_company_initiatives_approval_id.id,
            branch_id=koprol_setting.default_branch_initiatives_approval_id.id,
            divisi_id=koprol_setting.default_divisi_initiatives_approval_id.id,
            ).request_by_value(self, amount_approval)
        self.write({'state':'waiting_for_approval', 'approval_state':'rf'})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))
       

    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].sudo().get_per_branch(vals['branch_id'], 'IN')
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

    def action_create_new_quotation(self):
        form_id = self.env.ref('eps_proposal.eps_quotation_form_wizard_initiatives_view').id
        return {
            'name': ('Quotation'),
            'res_model': 'eps.quotation',
            'type': 'ir.actions.act_window',
            'context':{
                'default_initiatives_id': self.id,
            },
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': False,
        }  

    def action_create_tender(self):
        for record in self:
            self.env['eps.tender'].create({
                                    'initiatives_id' : record.id,
                                    'company_id': record.company_id.id,
                                    'branch_id': record.branch_id.id,
                                    'divisi_id': record.divisi_id.id,
                                    'department_id': record.department_id.id
                                    })

            record.write({'state': 'waiting_for_tender'})
        return True

    def _prepare_po_data(self):
        per_vendor = {}
        data = {}
        line = []
        for rec in self:
            for line in rec.initiatives_line_ids.filtered(lambda x: not x.purchase_lines):
                key = line.supplier_id
                if not per_vendor.get(key,False):
                    per_vendor[key] = {}
                    per_vendor[key]['order_line']=[]
                    per_vendor[key]['company_id']=rec.company_id.id
                    per_vendor[key]['branch_id']=rec.branch_id.id
                    per_vendor[key]['divisi_id']=rec.branch_id.id
                    per_vendor[key]['department_id']=rec.department_id.id
                    per_vendor[key]['initiatives_id']=rec.id
                    per_vendor[key]['partner_id']=line.supplier_id.id


                per_vendor[key]['order_line'].append([0,0,{
                    'branch_id': line.branch_id.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'date_planned': datetime.now(),
                    'product_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'taxes_id': [(6, 0, line.tax_id.ids)],
                    'initiatives_line_id': line.id
                    }])
                    
        return per_vendor

    def action_validate(self):
        """
        if initiative type == Kontrak Payung then create pricelist based on initiatives line
        
        if initiative type in Tender/One time purchase then create PR/Quotation/PO API to TOPS
        after that create PO in Odoo based on return value from TOPS's API

        """
        for rec in self:
            if not rec.initiatives_line_ids:
                raise ValidationError('Tidak ada detail inisiatif!')
            if rec.type=='Kontrak Payung':
                for line in rec.initiatives_line_ids:
                    self.env['product.supplierinfo'].create(line._prepare_vendor_pricelist())
            else:
                po_data = rec._prepare_po_data()
                for k,value in po_data.items():
                    self.env['purchase.order'].create(value)

            rec.write({'state': 'done'})

    def action_view_tender(self, tender=False):
        """This function returns an action that display existing tender of
        given initiatives ids. When only one found, show the initatives
        immediately.
        """
        if not tender:
            # initiatives_ids may be filtered depending on the user. To ensure we get all
            # initiatives related to the proposal, we read them in sudo to fill the
            # cache.
            tender = self.env['eps.tender'].search([('initiatives_id','=',self.id)])

        result = self.env['ir.actions.act_window']._for_xml_id('eps_proposal.eps_tender_action')
        # choose the view_mode accordingly
        if len(tender) > 1:
            result['domain'] = [('id', 'in', tender.ids)]
        # elif len(initiatives) == 1:
        else:
            res = self.env.ref('eps_proposal.eps_tender_form_view', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = tender.id
        

        return result

    def action_view_purchase(self, purchase=False):
        """This function returns an action that display existing tender of
        given initiatives ids. When only one found, show the initatives
        immediately.
        """
        if not purchase:
            # initiatives_ids may be filtered depending on the user. To ensure we get all
            # initiatives related to the proposal, we read them in sudo to fill the
            # cache.
            purchase = self.env['purchase.order'].search([('initiatives_id','=',self.id)])

        result = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_form_action')
        # choose the view_mode accordingly
        if len(purchase) > 1:
            result['domain'] = [('id', 'in', purchase.ids)]
        # elif len(initiatives) == 1:
        else:
            res = self.env.ref('purchase.purchase_order_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = purchase.id
        

        return result

class InitiativesLines(models.Model):
    _name = "eps.initiatives.line"
    _description = 'Initiatives Lines'

    branch_id = fields.Many2one('res.branch', string='Branch', required=True)
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives', ondelete='cascade')
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
    purchase_lines = fields.One2many('purchase.order.line', 'initiatives_line_id', string='Order Line')
    quotation_line_id = fields.Many2one('eps.quotation.line', string='Quotation Line')

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

    @api.onchange('supplier_id','product_id','quantity')
    def _onchange_supplier_product(self):
        if self.product_id and self.supplier_id:
            seller = self.product_id._select_seller(
            quantity=self.quantity,
            date=self.initiatives_id.date,
            partner_id=self.supplier_id
            )
            if seller:
                self.price_unit = seller.price
            else:
                self.price_unit = 0

    def _prepare_vendor_pricelist(self):
        data = {}
        for line in self:
            data = {
            'name': line.supplier_id.id,
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'price': line.price_unit,
            'initiatives_line_id': line.id,
            'initiatives_id': line.initiatives_id.id,
            'company_id': line.company_id.id,
            'date_start': line.initiatives_id.date_start,
            'date_end': line.initiatives_id.date_end
            }
        return data

            



