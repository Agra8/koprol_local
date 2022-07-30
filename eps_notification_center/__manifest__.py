{
    'name':"EPS - Notification Center",
    'version':'10.0.1.0.0',
    'depends':['eps_menu', 'eps_approval'],
    'author':"TRA",
    'category':"KOPROL",
    'description':"""
Notification Center
======
- Notification approval
    """,
    'data': [
        'views/eps_notification_center.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/eps_nc_res_config_settings.xml',
        'data/approval_mail_template.xml',
        'data/approval_mail_template_reminder.xml',
        'data/scheduled_actions_data.xml'
    ]
}