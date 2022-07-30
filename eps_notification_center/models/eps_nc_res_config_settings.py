from odoo import fields, models

class NcResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_email_template(self): 
        return self.env.ref('eps_notification_center.email_template_approval_notif')

    def _default_email_template_reminder(self): 
        return self.env.ref('eps_notification_center.email_template_approval_notif_reminder')

    email_template = fields.Many2one('mail.template', string='Email Template', config_parameter='eps_notification_center.email_template', default=_default_email_template)
    email_template_reminder = fields.Many2one('mail.template', string='Email Template Reminder', config_parameter='eps_notification_center.email_template_reminder', default=_default_email_template_reminder)
    wa_template = fields.Many2one('mail.template', string='WA Template', config_parameter='eps_notification_center.wa_template')
    sla_approval_proposal = fields.Integer(string='SLA Days Approval', config_parameter='eps_notification_center.sla_approval_proposal')