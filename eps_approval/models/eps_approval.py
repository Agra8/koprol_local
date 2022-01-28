from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
import operator
import qrcode
from odoo.tools import config
from odoo.http import request
from urllib.parse import quote

class eps_matrix_approval(models.Model):
    _name ="eps.matrix.approval"
    _description = "Matrix Approval"

    company_id = fields.Many2one('res.company', string='Company')         
    branch_id = fields.Many2one('res.branch','Cabang')
    divisi_id = fields.Many2one('eps.divisi','Divisi')
    department_id = fields.Many2one('hr.department','Department')
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
            ])
            search_full_ids = self.sudo().search([
                    ('company_id', '=', self.company_id.id),
                    ('branch_id', '=', self.branch_id.id),
                    ('divisi_id', '=' , self.divisi_id.id),
                    ('department_id', '=' , self.department_id.id),
                ])

            if (len(search_ids) > 0) or (len(search_full_ids) > 1):
                raise ValidationError("Matriks approval sudah dibuat!")
        else:
            search_ids = self.sudo().search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                ('divisi_id', '=' , self.divisi_id.id),
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

    def request_by_value(self,object,value,view_id=None,send_email=True):
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
        
        user_limit = 0
        min_value = min([x.limit for x in matrix])
        min_sequence = min([x.matrix_sequence for x in matrix])
        prev_sequence = 1
        state = 'IN'
        matrix_data = []
        

        for data in matrix :
            approval_start_date = False
            expected_date = False
            if data.matrix_sequence==min_sequence:
                state='IN'
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
            raise ValidationError(_('Nilai transaksi %d. Nilai terbersar di matrix approval: %d. Cek kembali Matrix Approval."'))
        if self._context.get('per_reviewer'):
            for rev in self._context.get('per_reviewer'):
                matrix_data.append(rev)
        
        sorted_matrix_data = sorted(matrix_data, key=operator.itemgetter('matrix_sequence', 'limit'))
        sequence = 1
        sla_approval = self.env['ir.config_parameter'].get_param('eps_notification_center.sla_approval_proposal')
        for i in sorted_matrix_data :
            i['sequence'] = sequence
            sequence+=1
        
        create_approval = self.env['eps.approval.transaction'].create(sorted_matrix_data)
        proposal_model = self.env['ir.model'].sudo().search([('model','=','eps.proposal')])
        if send_email:
            for approval in create_approval.filtered(lambda x:x.state=='IN'):
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

        for approval_line in approval_lines_ids:
            if approval_line.state == 'IN':
                if approval_line.group_id in user_groups:
                    if approval_line.limit > user_limit:
                        user_limit = approval_line.limit
                        approve_all = approval_line.value <= user_limit
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
        
        if user_limit:
            for approval_line in approval_lines_ids:
                if approval_line.state in ('IN','WA'):
                    if approve_all:
                        approval_line.write({
                        'state':'OK',
                        'user_id':self._uid,
                        'tanggal':datetime.now(),
                      })
                    elif approval_line.limit <= user_limit:
                        approval_line.write({
                        'state':'OK',
                        'user_id':self._uid,
                        'tanggal':datetime.now(),
                      })
                    
                    if approval_line.state == 'IN':
                        approval_line.approval_start_date = date.today()
                        self.send_notif_email(approval_line)
                        
                prev_sequence = approval_line.matrix_sequence
    
        if approve_all:
            return 1
        elif user_limit:
            return 2
        return 0

    def reject(self, trx, reason):
        user_groups = self.env['res.users'].browse(self._uid)['groups_id']
        approval_lines_ids = self.env['eps.approval.transaction'].search([
                                                            ('model_id','=',trx.__class__.__name__),
                                                            ('transaction_id','=',trx.id),
                                                          ],order="limit asc")
        if not approval_lines_ids:
            raise exceptions(('Perhatian !'), ("Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval."))
        
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
            raise exceptions(('Perhatian !'), ("Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval."))
        
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
        
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        qr_code = base_url+"/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s" % ('QR', quote(transaksi.get_full_url()), 150, 150)
        messages="""
            <p>Here's your outstanding approval on KOPROL:</p>
            <br/>
            <table>
                <tbody>
                    <tr>
                        <td>No</td>
                        <td>: 1 </td>
                        <td rowspan="4" align="center">
                            <img  width="100" height="100"  src="%s" /> """ % qr_code +"""
                        </td>
                    </tr>
                    <tr>
                        <td>Ticket #</td>
                        <td>: <a href="%s">%s</a> </td> """ % (transaksi.get_full_url(),str(transaksi.name)) +"""
                    </tr>
                    <tr>
                        <td>Subject</td>
                        <td>: %s </td> """ % str(transaksi.nama_proposal) +"""
                    </tr>
                    <tr>
                        <td>Entity</td>
                        <td>: %s </td> """ % str(transaksi.company_id.name) +"""
                    </tr>
                    <tr>
                        <td>Branch</td>
                        <td>: %s </td> """ % str(transaksi.branch_id.name) +"""
                    </tr>
                    <tr>
                        <td>Division</td>
                        <td>: %s </td> """ % str(transaksi.divisi_id.name) +"""
                        <td><i>Scan QR Code for detail & Approval</i></td>
                    </tr>
                    <tr>
                        <td>Requestor</td>
                        <td>: %s </td> """ % str(transaksi.employee_id.name) +"""
                    </tr>
                    <tr>
                        <td>Expected Date</td>
                        <td>: %s </td> """ % str(trx_id.expected_date) +"""
                    </tr>
                    <tr>
                        <td>Total</td>
                        <td>: Rp. %s </td> """ % str(trx_id.value) +"""
                    </tr>
                    <tr>
                        <td>Last Approval</td>
                        <td>: %s </td> """ % str(last_approval_user) +"""
                    </tr>
                    <tr>
                        <td>Aging Ticket</td>
                        <td>: 0 days </td>
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
        job_ids = self.env['hr.job'].search([('group_id','=',group.id)])
        cc_to = []
        cc_to.append([4, transaksi.employee_id.id, False])
        for job_id in job_ids:
            employees = self.env['hr.employee'].sudo().search([('job_id','=',job_id.id)])
            for employee in employees:
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
            proposal_model = self.env['ir.model'].sudo().search([('model','=','eps.proposal')])
            trxs = self.search([('approval_start_date','!=',date.today()), ('state','=','IN'), ('group_id','=',res_group['group_id']), ('model_id','=',proposal_model.id)])
            count = 1
            ins_trx = []
            messages+="<p>Here's your outstanding approval on KOPROL:</p>"
            for trx in trxs:
                transaksi = self.env[trx.model_id.model].sudo().browse(trx.transaction_id)
                get_usr = self.env['eps.approval.transaction'].sudo().search([('model_id','=',trx.model_id.id), ('transaction_id','=',trx.transaction_id), ('state','=','OK')], order = 'sequence DESC', limit = 1)
                if get_usr:
                    last_approval_user = get_usr.user_id.name
                else:
                    last_approval_user = "-"
                aging_ticket = datetime.now()+ timedelta(hours=7) - (trx.create_date + timedelta(hours=7))
                base_url = self.env["ir.config_parameter"].get_param("web.base.url")
                qr_code = base_url+"/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s" % ('QR', quote(transaksi.get_full_url()), 150, 150)
                messages+="""
                    <br/>
                    <table>
                        <tbody>
                            <tr>
                                <td>No</td>
                                <td>: %s </td> """ % str(count) +"""
                                <td rowspan="4" align="center">
                                    <img width="100" height="100" src="%s" /> """ % qr_code +"""
                                </td>
                            </tr>
                            <tr>
                                <td>Ticket #</td>
                                <td>: <a href="%s">%s</a> </td> """ % (transaksi.get_full_url(),str(transaksi.name)) +"""
                            </tr>
                            <tr>
                                <td>Subject</td>
                                <td>: %s </td> """ % str(transaksi.nama_proposal) +"""
                            </tr>
                            <tr>
                                <td>Entity</td>
                                <td>: %s </td> """ % str(transaksi.company_id.name) +"""
                            </tr>
                            <tr>
                                <td>Branch</td>
                                <td>: %s </td> """ % str(transaksi.branch_id.name) +"""
                                <td> </td>
                            </tr>
                            <tr>
                        <td>Division</td>
                            <td>: %s </td> """ % str(transaksi.divisi_id.name) +"""
                            <td><i>Scan QR Code for detail & Approval</i></td>
                        </tr>
                        <tr>
                            <td>Requestor</td>
                            <td>: %s </td> """ % str(transaksi.employee_id.name) +"""
                        </tr>
                            <tr>
                                <td>Expected Date</td>
                                <td>: %s </td> """ % str(trx.expected_date) +"""
                            </tr>
                            <tr>
                                <td>Total</td>
                                <td>: Rp. %s </td> """ % str(trx.value) +"""
                            </tr>
                            <tr>
                                <td>Last Approval</td>
                                <td>: %s </td> """ % str(last_approval_user) +"""
                            </tr>
                            <tr>
                                <td>Aging Ticket</td>
                                <td>: %s days </td> """ % str(aging_ticket.days) +"""
                            </tr>
                        </tbody>
                    </table>
                    <br/>
                """
                trx.reminder_counter += 1
                count += 1
                ins_trx.append([4, trx.id, False])
                
            messages+="""
                <hr />
                <i>This message is automaticaly generated by KOPROL System</i>
            """
            job_ids = self.env['hr.job'].search([('group_id','=',res_group['group_id'])])
            for job_id in job_ids:
                employees = self.env['hr.employee'].sudo().search([('job_id','=',job_id.id)])
                emp_cek = employees
                for employee in employees:
                    self.env['eps.notification.center'].sudo().create({
                        'approval_transaction_ids': ins_trx,
                        'form_id': trxs[0].view_id.id,
                        'transaction_id': trxs[0].transaction_id,
                        'subject' : "[KOPROL SYSTEM] OUTSTANDING APPROVAL KOPROL PER "+str(date.today()),
                        'message': messages,
                        'notify_to': employee.user_id.id,
                        'tipe_email': 'reminder'
                    })

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