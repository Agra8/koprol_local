from odoo import api, fields, models
from odoo.exceptions import ValidationError

class NotificationCenter(models.Model):
    _name = "eps.notification.center"
    _description = "Notification Center"

    approval_transaction_ids = fields.Many2many('eps.approval.transaction', 'eps_nc_approval_transaction_rel', 'notification_center_id', 'approval_transaction_id', string="Approval Trx id")
    form_id = fields.Many2one('ir.ui.view',string='Form View')
    transaction_id = fields.Integer('Transaction ID')
    tipe = fields.Selection([('wa','WA'),('email','Email')], string="Type", default='email')
    state = fields.Selection([('draft','Draft'),('sent','Sent')], string="State", default='draft')
    subject = fields.Char(string="Subject")
    message = fields.Text(string="Message")
    tipe_email = fields.Selection([('normal', 'Normal'),('reminder', 'Reminder')])
    cc_to = fields.Many2many('hr.employee', 'eps_nc_employee_rel', 'notification_center_id', 'employee_id', string="CC To")
    notify_to = fields.Many2one('res.users', string="Notify To")

    def action_sent_notif(self):
        if self.tipe_email == 'normal':
            template = self.env['ir.config_parameter'].get_param('eps_notification_center.email_template')
        else:
            template = self.env['ir.config_parameter'].get_param('eps_notification_center.email_template_reminder')
        if not template:
            raise ValidationError('Perhatian ! Template Email belum di atur')
        # template = self.env.ref('eps_notification_center.email_template_approval_notif')
        email_cc = str(tuple([c.work_email for c in self.cc_to])).replace(',)', '').replace('(','')
        mail = self.env['mail.template'].sudo().browse(int(template))
        mail_values = {
                    'subject': self.subject,
                    'notification': True,
                    'body_html': self.message,
                    'email_cc': email_cc
                }
        mail.send_mail(self.id, email_values=mail_values, force_send=True)
        self.write({'state' : 'sent'})