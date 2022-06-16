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
from datetime import datetime, timedelta
import pytz
from pytz import timezone

class Tender(models.Model):
    _name = "eps.tender"
    _description = 'Tender'
    _inherit = ['mail.thread']

    @api.model
    def _get_default_date(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    name = fields.Char(string='Proposal Name', required=True, default='/')
    initiatives_id = fields.Many2one('eps.initiatives', string='Initiatives', tracking=True, required=True)
    supplier_ids = fields.Many2many('res.partner', string='Supplier', domain="[('supplier_rank','=',1)]", tracking=True)
    tender_participant_ids = fields.One2many('eps.tender.participant','tender_id', string='Tender Participants', tracking=True)
    state = fields.Selection([
                            ('draft','Draft'),
                            ('aanweizing','Aanweizing'),
                            ('klarifikasi','Klarifikasi'),
                            ('final','Final'),
                            ('waiting_for_approval','Waiting for Approval'),
                            ('approved','Approved'),
                            ('closed','Closed')], default='draft',  string='State', tracking=True)
    date_start = fields.Datetime('Start Date', tracking=True)
    date_end = fields.Datetime('End Date', tracking=True)
    link_vicon = fields.Char('Link Vicon', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', related='initiatives_id.company_id', store=True, tracking=True)
    branch_id = fields.Many2one('res.branch', domain="[('company_id','=',company_id)]", string='Branch', related='initiatives_id.branch_id', store=True, tracking=True)
    divisi_id = fields.Many2one('eps.divisi', string='Divisi', related='initiatives_id.divisi_id', store=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', related='initiatives_id.department_id', store=True, tracking=True)
    quotation_line_ids = fields.One2many(related='initiatives_id.quotation_line_ids')
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','eps.tender')], copy=False)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    date = fields.Date('Date', required=True, tracking=True, default=_get_default_date)

    def action_aanweizing(self):
        for rec in self:
            rec.write({'state': 'aanweizing'})

    def action_klarifikasi(self):
        for rec in self:
            rec.write({'state': 'klarifikasi'})

    def action_final(self):
        for rec in self:
            rec.write({'state': 'final'})

    def action_close(self):
        for rec in self:
            rec.write({'state': 'closed'})

    def validity_check(self):
        for record in self:
            if not record.quotation_line_ids.filtered(lambda x:x.state=='proposed'):
                raise ValidationError('Tidak ada Quotation yang dipropose!')

    def action_request_approval(self):
        self.validity_check()
        self.env['eps.matrix.approval.line'].request_by_value(self, 10)
        self.write({'state':'waiting_for_approval', 'approval_state':'rf'})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
            self.initiatives_id.write({'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))
       

    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].sudo().get_per_branch(vals['branch_id'], 'TEN')
        vals['date'] = self._get_default_date()
        ids = super(Tender,self).create(vals)    
        return ids

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Tidak bisa hapus transaksi dalam status selain draft!'))
        return super(Tender, self).unlink()


class TenderParticipant(models.Model):
    _name = "eps.tender.participant"
    _description = 'Tender Participants'

    tender_id = fields.Many2one('eps.tender', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    type = fields.Selection([('User','User'),('Komite','Komite'),('Panitia','Panitia')], string='Type', required=True)
