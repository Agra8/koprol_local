#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from validate_email import validate_email

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import Warning,ValidationError

# 5: local imports

# 6: Import of unknown third party lib

STATES = [('draft', 'Draft'),('request_tunasid', 'Request Tunas ID'),('request_hondaid', 'Request Honda ID'),('approved', 'Approved'),('resign','Resign')]

class Employee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    # 7: defaults methods
    def _get_default_branch(self):
        branch_ids = False
        branch_ids = self.env.user.branch_ids
        if branch_ids and len(branch_ids) == 1:
            return branch_ids[0].id
        return False
    
    @api.model
    def _get_default_date(self):
        return self.env['res.branch'].get_default_date()

    # 8: fields
    nip = fields.Char(string='Nip', readonly=True, states={'draft': [('readonly', False)]}, help='')
    state = fields.Selection(selection=STATES, readonly=True, default=STATES[0][0],  string='State',  help='')
    is_user = fields.Boolean( string='Is user',  readonly=True, states={'draft' : [('readonly',False)]},  help='')
    user_login = fields.Char( string='User login',  readonly=True, states={'draft' : [('readonly',False)]},  help='')
    email = fields.Char(string='email')

    approve_uid = fields.Many2one(comodel_name='res.users',  string='Approve uid',  readonly=True, states={'draft' : [('readonly',False)]},  help='')
    approve_date = fields.Datetime( string='Approve date',  readonly=True, states={'draft' : [('readonly',False)]},  help='')

    # 8: relation fields
    job_id = fields.Many2one(comodel_name='hr.job',  string='Job',  readonly=True, states={'draft' : [('readonly',False)]},  help='',domain=[])
    branch_id = fields.Many2one(comodel_name='res.branch', default=_get_default_branch, string='Branch', readonly=True, states={'draft' : [('readonly',False)]},  help='' )
    area_id = fields.Many2one(comodel_name='res.area', string='Area',  states={'draft' : [('readonly',False)]},  help='')
    group_id = fields.Many2one(comodel_name='res.groups', string='Group',  readonly=True, states={'draft' : [('readonly',False)]},  help='')


    @api.onchange('job_id')
    def _onchange_job_id(self):
        if self.job_id:
            self.department_id = self.job_id.department_id.id

    @api.onchange('branch_id')
    def _onchange_branchId(self):
        domain={}
        self.area_id = False
        domain = {'area_id':[('branch_ids','=',0)]}
        if self.branch_id :
            if self._uid == 1 :
                domain = {'area_id':[('branch_ids','=',self.branch_id.id)]}
            else :
                domain = {'area_id':[('branch_ids','=',self.branch_id.id),('name','!=','ALL')]}
        return {'domain':domain}
        
    def action_confirm(self):
        self.state = STATES[1][0]
    
    def action_request_tunasid(self):
        self.state = 'requested_tunasid'

    def action_request_hondaid(self):
        self.state = 'request_hondaid'

    def action_approve(self):
        self.ensure_one()

        if not self.honda_id :
            return {
                'type': 'ir.actions.act_window',
                'name':'Honda ID',
                'res_model': 'hr.employee',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'view_id': self.env.ref('dms_employee.view_approve_honda_id_form').id,
                'res_id': self.id,     
            }
        else:
            self.write({
                'approve_uid': self._uid,
                'approve_date': self._get_default_date(),
                'state': 'approved',
                'source_sales_id': self.id,
            })
    
    def action_set_honda_id(self):   
        self.write({
            'approve_uid': self._uid,
            'approve_date': self._get_default_date(),
            'state': 'approved',
            'honda_id':self.honda_id,
            'source_sales_id': self.id,
        })
    
    @api.model
    def create(self,vals):
        group_id = False        
        jobs = False        
        if vals.get('job_id'):
            jobs = self.env['hr.job'].suspend_security().browse(vals['job_id'])
        if not jobs: 
            if vals.get('job_title'):
                jobs = self.env['hr.job'].suspend_security().search([('name','=',vals['job_title'])],limit=1)
                vals['job_id'] = vals.get('job_id') or jobs.id
                if not jobs:
                    raise Warning('Perhatian ! Job %s tidak ditemukan.' %vals.get('job_title'))
        
        group_id = jobs.group_id.id
        if not group_id: 
            raise Warning('Perhatian ! User Group belum diisi di Master Job.')
        return super(Employee,self).create(vals)
    
    def write(self, vals):
        if vals.get('job_id',False):
            if vals.get('job_id') != self.job_id.id:
                job = self.env['hr.job'].suspend_security().browse(vals['job_id'])
                self._message_log(body=_('<b>Job Changed!</b> From %s to %s') % (self.job_id.name,job.name))
                
            if self.user_id:
                self.user_id.suspend_security().groups_id = False
                if not job.group_id:
                    raise Warning('Perhatian ! User Group belum diisi di Master Job.')
                self.user_id.suspend_security().write({'groups_id':[(6,0,[job.group_id.id])]})
        return super(Employee,self).write(vals)
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning('Perhatian ! \n Data tidak bisa dihapus selain draft !')
        return super(Employee, self).unlink()