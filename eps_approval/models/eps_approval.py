from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.exceptions import ValidationError,Warning
from datetime import datetime, date, timedelta
import operator
import qrcode
from odoo.tools import config
from odoo.http import request
from urllib.parse import quote
from werkzeug.urls import url_encode

class eps_matrix_approval(models.Model):
    _name ="eps.matrix.approval"
    _description = "Matrix Approval"

    company_id = fields.Many2one('res.company', string='Company')         
    branch_id = fields.Many2one('res.branch','Cabang', domain="[('company_id','=',company_id)]")
    divisi_id = fields.Many2one('eps.divisi','Divisi', domain="[('company_id','=',company_id)]")
    department_id = fields.Many2one('hr.department','Department', domain="[('company_id','=',company_id)]")
    approval_line = fields.One2many('eps.matrix.approval.line','approval_id')
    view_id = fields.Many2one('ir.ui.view',string='Form View')
    model_id = fields.Many2one('ir.model',string='Form/Model')

    @api.constrains('company_id', 'branch_id', 'divisi_id')
    def _check_existance(self):
        if self.department_id.id:
            search_ids = self.sudo().search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                ('divisi_id', '=' , self.divisi_id.id),
                ('department_id', '=' , False),
                ('model_id', '=', self.model_id.id),
            ])
            search_full_ids = self.sudo().search([
                    ('company_id', '=', self.company_id.id),
                    ('branch_id', '=', self.branch_id.id),
                    ('divisi_id', '=' , self.divisi_id.id),
                    ('department_id', '=' , self.department_id.id),
                    ('model_id', '=', self.model_id.id),
                ])

            if (len(search_ids) > 0) or (len(search_full_ids) > 1):
                raise ValidationError("Matriks approval sudah dibuat!")
        else:
            search_ids = self.sudo().search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                ('divisi_id', '=' , self.divisi_id.id),
                ('model_id', '=', self.model_id.id),
            ])
            if len(search_ids) > 1:
                raise ValidationError("Matriks approval sudah dibuat!")

class eps_matrix_approval_line(models.Model):
    _name = "eps.matrix.approval.line"
    _order = "id asc"

    approval_id = fields.Many2one('eps.matrix.approval', string='Matrix Approval')
    matrix_sequence = fields.Integer(string='Sequence', default=10)
    limit = fields.Float(string='Limit')
    group_id = fields.Many2one('res.groups')
    model_id = fields.Many2one(related='approval_id.model_id', readonly=True)
    company_id = fields.Many2one(related='approval_id.company_id', readonly=True)
    branch_id = fields.Many2one(related='approval_id.branch_id', readonly=True)
    divisi_id = fields.Many2one(related='approval_id.divisi_id', readonly=True)
    department_id = fields.Many2one(related='approval_id.department_id', readonly=True)
    sla_days = fields.Integer('SLA Approval Days')

    def request_by_value(self,object,value,view_id=None):
        matrix_data = []
        if not self._context.get('bypass_check_master_approval'):
            if object.company_id and object.branch_id and not self._context.get('bypass_check_entity'):
                matrix = self.search([
                    ('model_id','=',object.__class__.__name__),
                    ('company_id','=',object['company_id'].id),
                    ('branch_id','=',object['branch_id'].id),
                    ('divisi_id','=',object['divisi_id'].id),
                    ('department_id','=',object['department_id'].id)
                  ],order="limit asc")
                
                if not matrix:
                    matrix = self.search([
                    ('model_id','=',object.__class__.__name__),
                    ('company_id','=',object['company_id'].id),
                    ('branch_id','=',object['branch_id'].id),
                    ('divisi_id','=',object['divisi_id'].id),
                  ],order="limit asc")
                    if not matrix:
                        raise Warning("Transaksi ini tidak memiliki matrix approval")
            else:
                matrix = self.search([
                    ('model_id','=',object.__class__.__name__),
                    ('company_id','=',self._context.get('company_id',False)),
                    ('branch_id','=',self._context.get('branch_id',False)),
                    ('divisi_id','=',self._context.get('divisi_id',False)),
                  ],order="limit asc")

                if not matrix:
                    raise Warning("Transaksi ini tidak memiliki matrix approval")
            
            user_limit = 0
            min_value = min([x.limit for x in matrix])
            min_sequence = min([x.matrix_sequence for x in matrix])
            prev_sequence = 1
            state = 'IN'
            
            first_record = True

            for data in matrix :
                approval_start_date = False
                expected_date = False
                if data.matrix_sequence==min_sequence:
                    if first_record:
                        state='IN'
                        first_record = False
                    else:
                        state='WA'
                    approval_start_date = date.today()
                    expected_date = date.today() + timedelta(days = data.sla_days)
                else:
                    state='IWA'

                matrix_data.append({
                  'value':value,
                  'group_id':data.group_id.id,
                  'transaction_id':object.id,
                  'model_id':data.model_id.id,
                  'limit':data.limit,
                  'state': state,
                  'view_id': view_id,
                  'company_id': data.company_id.id,
                  'branch_id': data.branch_id.id,
                  'divisi_id': data.divisi_id.id,
                  'department_id': data.department_id.id,
                  'matrix_sequence': data.matrix_sequence,
                  'expected_date': expected_date,
                  'approval_start_date': approval_start_date,
                  'sla_days': data.sla_days,
                })
                
                
                if user_limit < data.limit:
                    user_limit = data.limit

                prev_sequence=data.matrix_sequence
        
            if user_limit < value:
                #raise Warning(('Perhatian !'), ("Nilai transaksi %d. Nilai terbersar di matrix approval: %d. Cek kembali Matrix Approval.") % (value, user_limit))
                raise ValidationError(_('Nilai transaksi %d. Nilai terbersar di matrix approval: %d. Cek kembali Matrix Approval."' % (value, user_limit) ) )
        if self._context.get('per_reviewer'):
            for rev in self._context.get('per_reviewer'):
                matrix_data.append(rev)
        
        sorted_matrix_data = sorted(matrix_data, key=operator.itemgetter('matrix_sequence', 'limit'))
        sequence = 1
        for i in sorted_matrix_data :
            i['sequence'] = sequence
            sequence+=1
        
        create_approval = self.env['eps.approval.transaction'].create(sorted_matrix_data)
        proposal_model = self.env['ir.model'].sudo().search([('model','=','eps.proposal')])
        for approval in create_approval.filtered(lambda x:x.state=='IN'):
            if approval.model_id.id == proposal_model.id:
                self.send_notif_email(approval)
        return True

    def approve(self, trx):
        user_groups = self.env['res.users'].browse(self._uid)['groups_id']
        approval_lines_ids = self.env['eps.approval.transaction'].search([
                                                            ('model_id','=',trx.__class__.__name__),
                                                            ('transaction_id','=',trx.id),
                                                            ('state','in',('IWA','IN','WA'))
                                                          ],order="limit asc")
        if not approval_lines_ids:
            raise ValidationError('Perhatian ! Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval.')
        
        approve_all = False
        user_limit = 0
        prev_sequence = 1
        prev_state = ''
        last_approval = False

        for approval_line in approval_lines_ids:
            if approval_line.state == 'IN':
                if approval_line.group_id in user_groups:
                    if approval_line.limit > user_limit:
                        user_limit = approval_line.limit
                        approve_all = approval_line.value <= user_limit
                        last_approval = approval_line.group_id
                        approval_line.write({
                              'state':'OK',
                              'user_id':self._uid,
                              'tanggal':datetime.now(),
                            })
              
            elif approval_line.state=='OK':
                user_limit = approval_line.limit
                approve_all = approval_line.value <= user_limit

            elif approval_line.state=='WA':
                if prev_state == 'OK':
                    approval_line.write({
                              'state':'IN',
                              'approval_start_date': date.today(),
                              'expected_date': date.today() + timedelta(days = approval_line.sla_days),
                            })

                if approval_line.group_id in user_groups:
                    if approval_line.limit > user_limit:
                        user_limit = approval_line.limit
                        approve_all = approval_line.value <= user_limit
                
            elif approval_line.state=='IWA':
                if prev_state == 'OK':
                    approval_line.write({
                              'state':'IN',
                              'approval_start_date': date.today(),
                              'expected_date': date.today() + timedelta(days = approval_line.sla_days),
                            })
                elif prev_state in ('IN','WA') and prev_sequence == approval_line.matrix_sequence:
                    approval_line.write({
                              'state':'WA',
                            })
                

            prev_sequence = approval_line.matrix_sequence
            prev_state = approval_line.state
        
        proposal_model = self.env['ir.model'].sudo().search([('model','=','eps.proposal')])
        if user_limit:
            for approval_line in approval_lines_ids:
                if approval_line.state in ('IN','WA'):
                    if approve_all:
                        approval_line.write({
                        'state':'OK',
                        'user_id':self._uid,
                        'tanggal':datetime.now(),
                      })
                        last_approval = approval_line.group_id
                    elif approval_line.limit <= user_limit:
                        approval_line.write({
                        'state':'OK',
                        'user_id':self._uid,
                        'tanggal':datetime.now(),
                      })
                        last_approval = approval_line.group_id
                    
                    if approval_line.state == 'IN':
                        approval_line.approval_start_date = date.today()
                        if approval_line.model_id.id == proposal_model.id:
                            self.send_notif_email(approval_line)
                        
                prev_sequence = approval_line.matrix_sequence
    
        if approve_all:
            return 1
        elif user_limit:
            return {'last_approval':last_approval,'user_limit':user_limit}
        return 0

    def reject(self, trx, reason):
        user_groups = self.env['res.users'].browse(self._uid)['groups_id']
        approval_lines_ids = self.env['eps.approval.transaction'].search([
                                                            ('model_id','=',trx.__class__.__name__),
                                                            ('transaction_id','=',trx.id),
                                                          ],order="limit asc")
        if not approval_lines_ids:
            raise ValidationError("Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval.")
        
        reject_all = False
        for approval_line in approval_lines_ids:
            if approval_line.state in ('IN','WA'):
                if approval_line.group_id in user_groups:
                    reject_all = True
                    approval_line.write({
                      'state':'REJECT',
                      'reason':reason,
                      'user_id':self._uid,
                      'tanggal':datetime.now(),
                    })
                    break
        if reject_all:
            for approval_line in approval_lines_ids:
                if approval_line.state in ('IN','WA','IWA','OK'):
                    approval_line.write({
                  'state':'REJECT',
                  'user_id':self._uid,
                  'tanggal':datetime.now(),
                })
            return 1
        return 0
    
    def cancel_approval(self, trx, reason):
        user_groups = self.env['res.users'].browse(self._uid)['groups_id']
        approval_lines_ids = self.env['eps.approval.transaction'].search([
                                                            ('model_id','=',trx.__class__.__name__),
                                                            ('transaction_id','=',trx.id),
                                                          ],order="limit asc")
        if not approval_lines_ids:
            raise ("Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval.")
        
        reject_all = False
        for approval_line in approval_lines_ids:
            if approval_line.state in ('IN','WA'):
                reject_all = True
                approval_line.write({
                  'state':'CANCEL',
                  'reason':reason,
                  'user_id':self._uid,
                  'tanggal':datetime.now(),
                })
                break
        if reject_all:
            for approval_line in approval_lines_ids:
                if approval_line.state in ('IN','WA','IWA','OK'):
                    approval_line.write({
                      'state':'CANCEL',
                      'reason':reason,
                      'user_id':self._uid,
                      'tanggal':datetime.now(),
                })
            return 1
        return 0

    def send_notif_email(self, trx_id):
        transaksi = self.env[trx_id.model_id.model].sudo().browse(trx_id.transaction_id)
        ins_trx = []
        get_usr = self.env['eps.approval.transaction'].sudo().search([('model_id','=',trx_id.model_id.id), ('transaction_id','=',trx_id.transaction_id), ('state','=','OK')], order = 'sequence DESC', limit = 1)
        if get_usr:
            last_approval_user = get_usr.user_id.name
        else:
            last_approval_user = "-"
        
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        qr_code = base_url+"/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s" % ('QR', quote(transaksi.get_full_url()), 150, 150)
        url_discuss = {
            'action': self.env['ir.actions.actions'].sudo().search([('name','=','Discuss')], limit=1).id,
        }
        params = '/web?#%s' % url_encode(url_discuss)
        link_discuss = base_url + params
        link_discuss = link_discuss.replace('#','%23').replace('&','%26')
        now = datetime.now() + timedelta(hours=7)
        messages="""
            <p>Here's your outstanding approval on KOPROL:</p>
            <br/>
            <table>
                <tbody>
                    <tr>
                        <td colspan="3">Good %s"""% self.env['eps.approval.transaction'].get_part_of_day(now.hour) +""" </td>
                        <td rowspan="4" align="center">
                            <img  width="100" height="100"  src="%s" /> """ % qr_code +"""
                        </td>
                    </tr>
                    <tr>
                        <td>Ticket #</td>
                        <td>: </td>
                        <td><a href="%s">%s</a> </td> """ % (transaksi.get_full_url(),str(transaksi.name)) +"""
                    </tr>
                    <tr>
                        <td>Subject</td>
                        <td>: </td>
                        <td><a href="%s">%s</a> </td> """ % (transaksi.get_full_url(),str(transaksi.nama_proposal)) +"""
                    </tr>
                    <tr>
                        <td>Entity</td>
                        <td>: </td>
                        <td>%s </td> """ % str(transaksi.company_id.name) +"""
                    </tr>
                    <tr>
                        <td>Branch</td>
                        <td>: </td>
                        <td>%s </td> """ % str(transaksi.branch_id.name) +"""
                    </tr>
                    <tr>
                        <td>Division</td>
                        <td>: </td>
                        <td>%s </td> """ % str(transaksi.divisi_id.name) +"""
                        <td><i>Scan QR Code for detail & Approval</i></td>
                    </tr>
                    <tr>
                        <td>Requestor</td>
                        <td>: </td>
                        <td><a href="%s">%s</a> </td> """ % (str(link_discuss),str(transaksi.employee_id.name)) +"""
                    </tr>
                    <tr>
                        <td>Expected Date</td>
                        <td>: </td> 
                        <td>%s </td> """ % str(trx_id.expected_date) +"""
                    </tr>
                    <tr>
                        <td>Total Estimation</td>
                        <td>: </td>
                        <td>Rp. %s </td> """ % str(trx_id.value) +"""
                    </tr>
                    <tr>
                        <td>Description</td>
                        <td>: </td>
                        <td>%s</td> """ % str(transaksi.latar_belakang) +"""
                    </tr>
                </tbody>
            </table>
            <br/>
        """

        ins_trx.append([4, trx_id.id, False])
            
        messages+="""
            <hr />
            <i>This message is automaticaly generated by KOPROL System</i>
        """
        group = trx_id.group_id
        job_ids = self.env['hr.job'].sudo().search([('group_id','=',group.id)])
        cc_to = []
        cc_to.append([4, transaksi.employee_id.id, False])
        for job_id in job_ids:
            employees = self.env['hr.employee'].sudo().search([('job_id','=',job_id.id)])
            for employee in employees:
                if (transaksi.company_id in employee.user_id.company_ids) and (transaksi.branch_id in employee.user_id.branch_ids):
                    self.env['eps.notification.center'].sudo().create({
                        'approval_transaction_ids': ins_trx,
                        'form_id': trx_id.view_id.id,
                        'transaction_id': trx_id.transaction_id,
                        'message': messages,
                        'notify_to': employee.user_id.id,
                        'cc_to': cc_to,
                        'subject' : "[KOPROL SYSTEM - %s] %s" %(transaksi.name, transaksi.nama_proposal),
                        'tipe_email' : 'normal'
                    })

class eps_approval_transaction(models.Model):
    _name = "eps.approval.transaction"

    def _get_transaction_no(self):
        for rec in self:
            if rec.model_id.model in ('account.voucher','wtc.account.voucher','wtc.dn.nc'):
                rec.transaction_no = self.env[rec.model_id.model].browse(rec.transaction_id).number            
            else :
                rec.transaction_no = self.env[rec.model_id.model].browse(rec.transaction_id).name
        
    def _get_groups(self):
        x = self.env['res.users'].browse(self._uid)['groups_id']
        #is self.group_id in x ?
        self.is_mygroup = self.group_id in x 
    
    def _cek_groups(self,operator,value):
         
        group_ids = self.env['res.users'].browse(self._uid)['groups_id']
         
        if operator == '=' and value :
            where = [('group_id', 'in', [x.id for x in group_ids])]
        else :
            where = [('group_id', 'not in', [x.id for x in group_ids])]
 
        return where

    transaction_id = fields.Integer('Transaction ID')
    value = fields.Float('Value',digits=(12,2))
    model_id = fields.Many2one('ir.model',string='Form/Model')
    group_id = fields.Many2one('res.groups',string='Group')
    limit = fields.Float(string='Limit')
    user_id = fields.Many2one('res.users', string='User')
    tanggal = fields.Datetime(string='Tanggal')
    state = fields.Selection([('IN','In Progress'),('WA','Waiting'),('IWA','In Waiting'),('OK','Done'),('REJECT','Rejected'),('CANCEL','Cancelled')],string='State')
    matrix_sequence = fields.Integer(string='Sequence')
    company_id = fields.Many2one('res.company', string='Company')         
    branch_id = fields.Many2one('res.branch','Cabang')
    divisi_id = fields.Many2one('eps.divisi','Divisi')
    department_id = fields.Many2one('hr.department','Department')
    view_id = fields.Many2one('ir.ui.view',string='Form View')
    reason = fields.Text('Reason')
    reminder_counter = fields.Integer(string='Reminder Counter', default=0)
    expected_date = fields.Date(string='Expected Date')
    sequence = fields.Integer(string='Integer')
    approval_start_date = fields.Date(string='Start Date')
    sla_days = fields.Integer('SLA Approval Days')
    transaction_no = fields.Char(string="Transaction No")
    is_mygroup = fields.Boolean(compute='_get_groups', string="is_mygroup", method=True, search='_cek_groups')

    @api.model
    def create(self,vals):
        model_id = self.env['ir.model'].browse(vals.get('model_id'))
        if model_id.model in ('account.voucher','wtc.account.voucher','wtc.dn.nc'):
            vals['transaction_no'] = self.env[model_id.model].browse(vals.get('transaction_id')).number            
        else :
            vals['transaction_no'] = self.env[model_id.model].browse(vals.get('transaction_id')).name 
        ids = super(eps_approval_transaction,self).create(vals) 

        return ids


        
    def get_part_of_day(self,h):
        return (
            "Morning"
            if 5 <= h <= 11
            else "Afternoon"
            if 12 <= h <= 17
            else "Evening"
            if 18 <= h <= 22
            else "Night"
        )
    
    def schedule_notification_outstanding_proposal_approval(self):
       
        get_group = """
            SELECT group_id from eps_approval_transaction
            WHERE approval_start_date != '%s' AND state = 'IN'
            GROUP BY group_id
        """ % str(date.today())
        self._cr.execute (get_group)
        res_groups =  self._cr.dictfetchall()
        messages = ""
        for res_group in res_groups:
            group_obj = self.env['res.groups'].browse(res_group['group_id'])
            for user in group_obj.users:
                proposal_model = self.env['ir.model'].sudo().search([('model','=','eps.proposal')])
                trxs = self.search([('approval_start_date','!=',date.today()), ('state','=','IN'), ('group_id','=',group_obj.id), ('model_id','=',proposal_model.id), ('company_id', 'in', [c.id for c in user.company_ids]), ('branch_id', 'in', [c.id for c in user.branch_ids])])
                count = 1
                ins_trx = []
                base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                url_params = {
                    'view_type': 'form',
                    'model': 'eps.proposal',
                    'menu_id': self.env.ref('eps_menu.eps_proposal_top_menu').id,
                    'action': self.env.ref('eps_proposal.eps_proposal_action').id,
                }
                params = '/web?#%s' % url_encode(url_params)
                full_url = base_url + params
                full_url = full_url.replace('#','%23').replace('&','%26')

                qr_code = base_url+"/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s" % ('QR', quote(full_url), 150, 150)
                now = datetime.now() + timedelta(hours=7)
                messages+="""
                    <table>
                        <tr>
                            <td colspan="3">
                                <p>Good %s</p>"""% self.get_part_of_day(now.hour) +"""
                                <br/>
                                <table>
                                    <tr>
                                        <td>Nama</td>
                                        <td>:</td>
                                        <td>%s</td> """ %user.name+"""
                                    </tr>
                                    <tr>
                                        <td>Role</td>
                                        <td>:</td>
                                        <td>%s</td> """ %group_obj.name+"""
                                    </tr>
                                    <tr>
                                        <td>Total Outstanding</td>
                                        <td>:</td>
                                        <td>%s</td> """ %str(len(trxs))+"""
                                    </tr>
                                </table>
                            </td>
                            <td colspan="3" align="center">
                                <img width="100" height="100" src="%s" /> """ % qr_code +"""
                                <br/>
                                <i>Scan QR Code for detail & Approval</i>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="6">
                                <br/>
                            </td>
                        <tr>
                        <tr>
                            <td colspan="6">
                                <p>Here's your outstanding approval on KOPROL:</p>
                            </td>
                        <tr>
                            <td style="border:1px solid black; padding:10px">No.</td>
                            <td style="border:1px solid black; padding:10px">Ticket #</td>
                            <td style="border:1px solid black; padding:10px">Subject</td>
                            <td style="border:1px solid black; padding:10px">Expected Date</td>
                            <td style="border:1px solid black; padding:10px">Total</td>
                            <td style="border:1px solid black; padding:10px">Aging</td>
                        </tr>
                """
                for trx in trxs:
                    transaksi = self.env[trx.model_id.model].sudo().browse(trx.transaction_id)
                    get_usr = self.env['eps.approval.transaction'].sudo().search([('model_id','=',trx.model_id.id), ('transaction_id','=',trx.transaction_id), ('state','=','OK')], order = 'sequence DESC', limit = 1)
                    if get_usr:
                        last_approval_user = get_usr.user_id.name
                    else:
                        last_approval_user = "-"
                    selisih = date.today() - trx.approval_start_date
                    aging_ticket = int(selisih.days) - int(trx.sla_days)
                    if aging_ticket < 0:
                        aging_ticket = 0
                    messages+="""
                            <tr>
                                <td style="border:1px solid black; padding:10px">%s </td> """ % str(count) +"""
                                <td style="border:1px solid black; padding:10px">%s </td> """ % str(transaksi.name) +"""
                                <td style="border:1px solid black; padding:10px">%s </td> """ % str(transaksi.nama_proposal) +"""
                                <td style="border:1px solid black; padding:10px">%s </td> """ % str(trx.expected_date) +"""
                                <td style="border:1px solid black; padding:10px">Rp. %s </td> """ % str(trx.value) +"""
                                <td style="border:1px solid black; padding:10px">%s days </td> """ % str(aging_ticket) +"""
                            </tr>
                    """
                    trx.reminder_counter += 1
                    count += 1
                    ins_trx.append([4, trx.id, False])
                    
                messages+="""
                        </table>
                        <br/>
                    <hr />
                    <i>This message is automaticaly generated by KOPROL System</i>
                """
                
                self.env['eps.notification.center'].sudo().create({
                    'approval_transaction_ids': ins_trx,
                    'form_id': trxs[0].view_id.id,
                    'transaction_id': trxs[0].transaction_id,
                    'subject' : "Outstanding Approval on KOPROL System per "+str(date.today()),
                    'message': messages,
                    'notify_to': user.id,
                    'tipe_email': 'reminder'
                })
                messages=""

    def get_transaction(self):  
        query = """
                SELECT perm_read
                FROM ir_model_access 
                WHERE model_id = %s
                AND group_id IN (SELECT hid FROM res_groups_implied_rel WHERE gid = %s)
            """ % (self.model_id.id, self.group_id.id)
        self._cr.execute(query)
        ress = self._cr.fetchall()
        if len(ress) < 1 :
            return False
        if any([x[0] for x in ress]) :
            if self.view_id == False :
                return {
                    'name': self.model_id.name,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': self.model_id.model,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'res_id': self.transaction_id
                    }  
            else :
                return {
                    'name': self.model_id.name,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': self.model_id.model,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'res_id': self.transaction_id,
                    'view_id':self.view_id.id
                    }
        else :
            return False
    

class eps_reject_approval(models.TransientModel):
    _name = "eps.reject.approval"
   
    reason = fields.Text('Reason')
    
    def eps_reject_approval(self, context=None):
        if context == None:
            context = self._context
        user = self.env['res.users'].browse(self._uid)['groups_id']
        trx_id = context.get('active_id',False) #When you call any wizard then in this function ids parameter contain the list of ids of the current wizard record. So, to get the purchase order ID you have to get it from context.
        model_name = context.get('model_name',False)
        next_workflow = context.get('next_workflow',False)
        update_value = context.get('update_value',False)
        
        if not trx_id and not model_name:
            raise Warning('Perhatian ! Context approval belum lengkap')
        
        trx_obj = self.env[model_name].browse(trx_id)
        if self.env['eps.matrix.approval.line'].reject(trx_obj, self.reason):
            if next_workflow:
                workflow.trg_validate(self._uid, model_name, trx_id, next_workflow, self._cr) 
            elif update_value :
                trx_obj.write(update_value)
        else :
            raise Warning('Perhatian ! User tidak termasuk group approval')
                                                      
        return True 
    
class eps_cancel_approval(models.TransientModel):
    _name = "eps.cancel.approval"
   
    reason = fields.Text('Reason')
    
    def eps_cancel_approval(self, context=None):
        if context == None:
            context = self._context
        user = self.env['res.users'].browse(self._uid)['groups_id']
        trx_id = context.get('active_id',False) #When you call any wizard then in this function ids parameter contain the list of ids of the current wizard record. So, to get the purchase order ID you have to get it from context.
        model_name = context.get('model_name',False)
        next_workflow = context.get('next_workflow',False)
        update_value = context.get('update_value',False)
        
        if not trx_id and not model_name:
            raise Warning('Perhatian ! Context approval belum lengkap')
        
        trx_obj = self.env[model_name].browse(trx_id)
        if self.env['eps.matrix.approval.line'].cancel_approval(trx_obj, self.reason):
            if next_workflow:
                workflow.trg_validate(self._uid, model_name, trx_id, next_workflow, self._cr) 
            elif update_value :
                trx_obj.write(update_value)
        else :
            raise Warning('Perhatian ! User tidak termasuk group approval')
                                                      
        return True
    
class eps_cancel_approved(models.TransientModel):
    _name = "eps.cancel.approved"
   
    reason = fields.Text('Reason')
    
    def eps_cancel_approved(self, context=None):
        if context == None:
            context = self._context
        user = self.env['res.users'].browse(self._uid)['groups_id']
        trx_id = context.get('active_id',False) #When you call any wizard then in this function ids parameter contain the list of ids of the current wizard record. So, to get the purchase order ID you have to get it from context.
        model_name = context.get('model_name',False)
        next_workflow = context.get('next_workflow',False)
        update_value = context.get('update_value',False)
        
        if not trx_id and not model_name:
            raise Warning('Perhatian ! Context approval belum lengkap')
        
        reject_reason = "batal approve: "+self.reason
        trx_obj = self.env[model_name].browse(trx_id)
        for approval_line in trx_obj.approval_ids:
            approval_line.write({'state':'CANCEL'})
        
        form_id = self.env['ir.model'].search([('model','=', model_name)])
        history = self.env['eps.approval.transaction'].create({
                                                                'model_id': form_id.id,
                                                                'state':'CANCEL', 
                                                                'transaction_id': trx_id, 
                                                                'user_id': self._uid, 
                                                                'reason': reject_reason,
                                                                'tanggal':datetime.now()})
        if next_workflow:
            workflow.trg_validate(self._uid, model_name, trx_id, next_workflow, self._cr) 
        elif update_value :
            trx_obj.write(update_value)                                              
        return True 