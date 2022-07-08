from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError,Warning
import subprocess
import base64
import os
import platform
from odoo.tools import config
from datetime import datetime, date, timedelta
import qrcode
from werkzeug.urls import url_encode
from io import BytesIO
import pytz
from pytz import timezone
import json

class Proposal(models.Model):
    _name = "eps.proposal"
    _description = 'Proposal'
    _inherit = ['mail.thread']

    @api.depends('initiatives_ids.proposal_id')
    def _compute_initiatives(self):
        for record in self:
            record.initiatives_count = len(record.initiatives_ids.ids)

    @api.model
    def _get_default_date(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    
    name = fields.Char(string='Proposal Name', required=True, default='/')
    date = fields.Date(string='Tanggal Proposal', required=True, default=_get_default_date)
    nama_proposal = fields.Char(string='Nama Proposal', required=True, tracking=True)
    state = fields.Selection(selection=[('draft','Draft'),('waiting_for_approval','Waiting for Approval'),('approved','Approved'),('rejected','Rejected'),('done','Done')],default='draft',  string='State',  help='', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, tracking=True)
    branch_id = fields.Many2one('res.branch', string='Branch', required=True, tracking=True, domain="[('company_id','=',company_id)]")
    divisi_id = fields.Many2one('eps.divisi', string='Divisi', required=True, tracking=True, domain="[('company_id','=',company_id)]")
    department_id = fields.Many2one('hr.department', domain="[('company_id','=',company_id)]", string='Department', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='PIC', required=True, tracking=True)
    pic_contact = fields.Char(related='employee_id.mobile_phone', string="PIC's Contact", tracking=True)
    latar_belakang = fields.Text(string='Latar Belakang', tracking=True)
    sasaran_tujuan = fields.Text(string='Sasaran dan Tujuan', tracking=True)
    rencana_pengajuan = fields.Text(string='Rencana Pengajuan', tracking=True)
    # estimasi_biaya = fields.Text(string='Estimasi Biaya')
    proposal_line_ids = fields.One2many('eps.proposal.line', 'proposal_id', string='Lines')
    total = fields.Float(string='Total (grandtotal exclude PPN)', compute='_compute_total', tracking=True)
    file_document = fields.Binary(string="File Document")
    filename_document = fields.Char(string="File Document")
    filename_upload_document = fields.Char(string="Filename upload Document")
    file_document_show = fields.Binary(string="File Document", compute='_compute_file_document')
    requested_by = fields.Many2one('res.users', string='Requested by')
    requested_on = fields.Datetime(string='Requested on')
    closed_by = fields.Many2one('res.users', string='Closed by')
    closed_on = fields.Datetime(string='Closed on')
    printout_file = fields.Binary(string="Printout File")
    printout_filename = fields.Char(
        string='Printout Filename',
        required=False)
    approval_ids = fields.One2many('eps.approval.transaction', 'transaction_id', string='Approval', domain=[('model_id','=','eps.proposal')], copy=False)
    approval_state = fields.Selection([('b','Belum Request'),('rf','Request For Approval'),('a','Approved'),('r','Reject')],'Approval State', readonly=True)
    initiatives_ids = fields.One2many('eps.initiatives', 'proposal_id', string='Initiatives', copy=False)
    initiatives_count = fields.Integer(compute="_compute_initiatives", string='Initiatives Count', copy=False, default=0, store=True)
    expected_date = fields.Date('Expected Date')
    type = fields.Selection([('category','Category'),('product','Product')], string='Type', default='category', required=True)
    proposal_product_line_ids = fields.One2many('eps.proposal.product.line', 'proposal_id', string='Product Lines')

    # @api.onchange('company_id')
    # def _onchange_company(self):
    #     if self.company_id:
    #         branch_ids = [b.id for b in self.env.user.branch_ids.filtered(lambda x:x.company_id.id==self.company_id.id)]
    #         print (branch_ids,"<<<<<<<<<<<<<<branch_ids")
    #         return {'domain' : {'branch_id':[('id','in',branch_ids)],},}

    # def get_custom_domain(self):
    #     domain = False
    #     if self.env.uid != SUPERUSER_ID:
    #         context = self._context or {}
    #         domain = ('id','=', False)
    #         branch_employee = self.env.user.branch_ids
    #         if branch_employee:
    #             domain = False
    #             active_employee = branch_employee[0]
    #             branch_ids = branch_employee.ids
    #             domain = ('branch_id','in', branch_ids)
    #         return domain

    # @api.model
    # def read_group(self, domain, fields, groupby, offset = 0, limit=None, orderby=False, lazy=True):
    #     custom_domain = self.get_custom_domain()
    #     if custom_domain:
    #         domain.append(custom_domain)
    #     return super(Proposal, self).read_group(domain, fields, groupby, offset = offset, limit=limit, orderby=orderby, lazy=lazy)

    # @api.model
    # def _search(self, args, offset = 0, limit=None, order=None, count=False, access_rights_uid=None):
    #     custom_domain = self.get_custom_domain()
    #     if custom_domain:
    #         args.append(custom_domain)
    #     return super(Proposal, self)._search(args, offset, limit, order, count, access_rights_uid)

    @api.onchange('type')
    def _onchange_type(self):
        if self.type:
            self.proposal_product_line_ids = False

    @api.depends('proposal_line_ids.price')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(x.price for x in rec.proposal_line_ids)

    @api.depends('filename_upload_document')
    def _compute_file_document(self):
        if self.filename_upload_document:
            image_document = self.env['eps.config.files'].sudo().get_img(self.filename_upload_document)
            self.file_document_show = image_document
        else : 
            self.file_document_show = False

    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].sudo().get_per_branch(vals['branch_id'], 'PRO')
        if vals.get('file_document'):
            file_document = vals['file_document']
            vals['file_document'] = False
        else:
            file_document = False

        vals['date'] = self._get_default_date()

        ids = super(Proposal,self).create(vals)    
        if file_document:
            tmp_kk = vals['filename_document'].split('.')
            ext = tmp_kk[len(tmp_kk) - 1]
            if ext not in ('pdf', 'PDF'):
                raise Warning('Maaf, format file harus pdf')
            filename_document = str('eps_proposal_')+str(ids.id)+'.'+ext
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
        return super(Proposal,self).write(vals)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Tidak bisa hapus transaksi dalam status selain draft!'))
        return super(Proposal, self).unlink()

    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url_params = {
            'id': self.id,
            'view_type': 'form',
            'model': self._name,
            'menu_id': self.env.ref('eps_menu.eps_proposal_top_menu').id,
            'action': self.env.ref('eps_proposal.eps_proposal_action').id,
        }
        params = '/web?#%s' % url_encode(url_params)
        full_url = base_url + params
        # full_url = full_url.replace('#','%23').replace('&','%26')
        return full_url

    def generate_qr_code(self, text, img_name, template):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        data_dir = config['data_dir']
        file_path = f'{data_dir}/{img_name}.png'
        img.save(file_path)
        img = InlineImage(tpl=template,
            image_descriptor=file_path,
            width=Mm(40),
            height=Mm(40))
        return img

    def button_print(self):
        return self.env.ref('eps_proposal.action_report_eps_proposal').report_action(self)

    def button_print_old(self):
        self.ensure_one()
        data_dir = config['data_dir']
        working_dir = os.path.dirname(__file__)
        filename_doc = f'Proposal {datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.docx'
        filename_pdf = f'Proposal {datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.pdf'
        if platform.system() != 'Linux':
            template_path = working_dir.replace('\\models', '\\templates\\printout_proposal.docx')
            file_path = f'{data_dir}\\{filename_doc}'
        else :
            template_path = working_dir.replace('/models', '/templates/printout_proposal.docx')
            file_path = f'{data_dir}/{filename_doc}'

        template = DocxTemplate(template_path)
        lines = []
        for line in self.proposal_line_ids :
            lines.append({
                'categ_name': line.categ_id.name,
                'price': '{:,.2f}'.format(line.price),
            })
        datas = {
            'date': self.date or '',
            'company_name': self.company_id.name or '',
            'branch_name': self.divisi_id.name or '',
            'doc_no': self.name or '',
            'perihal': self.nama_proposal or '',
            'background': self.latar_belakang or '',
            'objective': self.sasaran_tujuan or '',
            'rencana_pengajuan': self.rencana_pengajuan or '',
            'qr_url': self.generate_qr_code(text=self.get_full_url(), img_name='qr_url', template=template),
            'total': '{:,.2f}'.format(self.total),
            'lines': lines,
        }
        template.render(datas, autoescape=True)
        template.save(file_path)
        if platform.system() != 'Linux':
            try:
                convert(f'{data_dir}\\{filename_doc}', f'{data_dir}\\{filename_pdf}')
                file_path = file_path.replace('docx', 'pdf')
                printout_filename = 'Proposal.pdf'
            except:
                pass # jika gagal filepath tetap docx
                printout_filename = 'Proposal.docx'
        else:
            self.doc2pdf_linux(data_dir, file_path)
            file_path = file_path.replace('docx', 'pdf')
            printout_filename = 'Proposal.pdf'
        generated = False
        # convert doc to pdf perlu waktu beberapa milisecond, sehingga tidak langsung terbaca
        while not generated:
            try:
                fp = open(file_path, "rb")
                generated = True
            except:
                generated = False
        file_data = fp.read()
        out = base64.encodebytes(file_data)
        self.write({
            'printout_file': out,
            'printout_filename': printout_filename,
        })
        fp.close()
        url = "web/content/?model=" + self._name + "&id=" + str(
            self.id) + "&field=printout_file&download=true&filename=" + self.printout_filename
        return {
            'name': 'Proposal',
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def doc2pdf_linux(self, data_dir, doc):
        cmd = f'libreoffice --convert-to pdf --outdir {data_dir}'.split() + [doc]
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        p.wait(timeout=10)
        p.communicate()

    def validity_check(self):
        if not self.proposal_line_ids:
            raise ValidationError('Category proposal belum diisi!')

    def _prepare_proposal_line(self, proposal_product_line_ids):
        data = []
        per_categ = {}
        for line in proposal_product_line_ids:
            if not line.product_id.categ_id.proposal_categ_id:
                raise ValidationError('Proposal category untuk product %s belum disetting, silahkan menghubungi departement GA!' % line.product_id.name)
            
            key = line.product_id.categ_id.proposal_categ_id.id
            if not per_categ.get(key,False):
                per_categ[key] = {}
            per_categ[key]['price']=per_categ[key].get('price',0)+line.price_total

        for key,value in per_categ.items():
            data.append([0,False,{
                'categ_id': key,
                'price': value['price']
                }])
        return data


    def action_request_approval(self):
        reviewer_approval = {}
        per_reviewer = []

        if self.type=='product' and self.proposal_product_line_ids:
            if self.proposal_line_ids:
                self._cr.execute('delete from eps_proposal_line where proposal_id=%s' % self.id)
            proposal_line = self._prepare_proposal_line(self.proposal_product_line_ids)
            self.proposal_line_ids = proposal_line

        self.validity_check()

        for line in self.proposal_line_ids.filtered(lambda x:x.categ_id.group_id and x.categ_id.group_id.id):
            key = line.categ_id.group_id.id
            if not reviewer_approval.get(key,False):
                reviewer_approval[key] = {}
                reviewer_approval[key]['reviewer_sequence']=line.categ_id.matrix_sequence
                reviewer_approval[key]['reviewer_value']=line.categ_id.limit
                reviewer_approval[key]['reviewer_sla_days']=line.categ_id.sla_days

        for key, value in reviewer_approval.items():
            per_reviewer.append({'value':self.total,
              'group_id':key,
              'transaction_id':self.id,
              'model_id': self.env['ir.model'].search([('model','=',self.__class__.__name__)]).id,
              'limit': value['reviewer_value'],
              'state': 'IWA',
              'view_id': False,
              'company_id': self.company_id.id,
              'branch_id': self.branch_id.id,
              'divisi_id': self.divisi_id.id,
              'department_id': self.department_id.id,
              'matrix_sequence': value['reviewer_sequence'],
              'sla_days': value['reviewer_sla_days']
              })

        self.env['eps.matrix.approval.line'].with_context(per_reviewer=per_reviewer).request_by_value(self, self.total)
        sla_proposal = self.env['ir.config_parameter'].sudo().get_param('eps_notification_center.sla_approval_proposal')
        expected_date = date.today() + timedelta(days = int(sla_proposal))
        self.write({'state':'waiting_for_approval', 'approval_state':'rf', 'expected_date': expected_date})

    def action_approve(self):
        approval_sts = self.env['eps.matrix.approval.line'].approve(self)
        if approval_sts == 1 :
            self.write({'approval_state':'a', 'state':'approved'})
        elif approval_sts == 0 :
            raise ValidationError(_('User tidak termasuk group Approval'))

    def action_view_initiatives(self, initiatives=False):
        """This function returns an action that display existing initatives of
        given proposal ids. When only one found, show the initatives
        immediately.
        """
        if not initiatives:
            # initiatives_ids may be filtered depending on the user. To ensure we get all
            # initiatives related to the proposal, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['initiatives_ids'])
            initiatives = self.initiatives_ids

        result = self.env['ir.actions.act_window']._for_xml_id('eps_proposal.eps_initiatives_action')
        # choose the view_mode accordingly
        if len(initiatives) > 1:
            result['domain'] = [('id', 'in', initiatives.ids)]
        # elif len(initiatives) == 1:
        else:
            res = self.env.ref('eps_proposal.eps_initiatives_form_view', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = initiatives.id
        

        return result

    def get_aging(self, approval_date, approved_date=False):
        aging = 0
        if approval_date :
            if approved_date:
                date_now = approved_date.date()
            else:
                date_now = datetime.now().date()
            delta = date_now - approval_date
            aging = delta.days
        if aging :
            if aging == 1 :
                aging = f'{aging} day'
            else :
                aging = f'{aging} days'
        return aging

    def get_state(self):
        state = (dict(self._fields['state'].selection).get(self.state)).upper()
        state = state.replace('WAITING FOR APPROVAL', 'WFA')
        return state

class ProposalLine(models.Model):
    _name = 'eps.proposal.line'
    _description = 'Proposal Line'
    _rec_name = 'categ_id'

    @api.depends('initiatives_ids.state','initiatives_ids.amount_total')
    def _compute_reserved_amount(self):
        for rec in self:
            rec.reserved_amount = sum(x.amount_total for x in rec.initiatives_ids.filtered(lambda y: y.state=='done'))

    proposal_id = fields.Many2one('eps.proposal', string='Proposal', ondelete='cascade')
    categ_id = fields.Many2one('eps.category', string='Proposal Category', required=True)
    price = fields.Float(string='Unit Price')
    file_penawaran = fields.Binary(string="File Penawaran")
    filename_penawaran = fields.Char(string="Filename Penawaran")
    filename_upload_penawaran = fields.Char(string="Filename upload Penawaran")
    file_penawaran_show = fields.Binary(string="File Penawaran", compute='_compute_file_penawaran' ,help="")
    reserved_amount = fields.Float(compute=_compute_reserved_amount, store=True, string='Reserved Amount')
    initiatives_ids = fields.One2many('eps.initiatives','proposal_line_id', string='Detail Initiatives')

    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price<=0:
                raise ValidationError('Unit Price harus >0')

    @api.depends('filename_upload_penawaran')
    def _compute_file_penawaran(self):
        for rec in self:
            if rec.filename_upload_penawaran:
                image_document = rec.env['eps.config.files'].sudo().get_img(rec.filename_upload_penawaran)
                rec.file_penawaran_show = image_document
            else : 
                rec.file_penawaran_show = False

    @api.model
    def create(self,vals):
        if vals.get('file_penawaran'):
            file_penawaran = vals['file_penawaran']
            vals['file_penawaran'] = False
        else:
            file_penawaran = False
        
        ids = super(ProposalLine,self).create(vals)    
        if file_penawaran:
            tmp_kk = vals['filename_penawaran'].split('.')
            ext = tmp_kk[len(tmp_kk) - 1]
            if ext not in ('pdf', 'PDF'):
                raise Warning('Maaf, format file harus pdf')
            filename_penawaran = str('eps_proposal_line_')+str(ids.id)+'.'+ext
            self.env['eps.config.files'].sudo().upload_file(filename_penawaran, file_penawaran)
            ids.filename_upload_penawaran=filename_penawaran
        return ids

    def write(self,vals):
        if vals.get('file_penawaran'):
            file_penawaran = vals['file_penawaran']
            vals['file_penawaran'] = False
            tmp_kk = vals['filename_penawaran'].split('.')
            ext = tmp_kk[len(tmp_kk) - 1]
            if ext not in ('pdf', 'PDF'):
                raise Warning('Maaf, format file harus pdf')
            filename_penawaran_up = str('eps_proposal_line_')+str(self.id)+'.'+ext
            self.env['eps.config.files'].upload_file(filename_penawaran_up, file_penawaran)
            vals['filename_upload_penawaran']=filename_penawaran_up
        return super(ProposalLine,self).write(vals)

class ProductLine(models.Model):
    _name = "eps.proposal.product.line"
    _description = 'Proposal Product Lines'

    def _get_default_branch(self):
        return self._context.get('branch_id',False)


    proposal_id = fields.Many2one('eps.proposal', string='Proposal', required=True, ondelete='cascade')
    branch_id = fields.Many2one('res.branch', string='Branch', required=True, default=_get_default_branch)
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True)
    product_id = fields.Many2one('product.product', string='Item', required=True)
    quantity = fields.Float('Quantity')
    price_unit = fields.Float('Unit Price')
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    company_id = fields.Many2one('res.company', related='proposal_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related='proposal_id.company_id.currency_id', store=True, string='Currency', readonly=True)

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        """
        Compute the amounts of the Initiatives line.
        """
        for line in self:
            price_total = line.price_unit * line.quantity
            line.update({
                'price_total': price_total,
            })

    @api.onchange('product_id','quantity')
    def _onchange_product_quantity(self):
        if self.product_id and self.company_id:
            seller = self.product_id.with_company(self.company_id)._select_seller(
            quantity=self.quantity,
            date=self.proposal_id.date,
            )
            if seller:
                self.price_unit = seller.price
                self.supplier_id = seller.name.id
            else:
                self.price_unit = 0