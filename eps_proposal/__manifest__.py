{
    'name':"EPS - Proposal",
    'version':'10.0.1.0.0',
    'depends':['eps_menu', 'eps_config_files','eps_branch','eps_approval', 'mail', 'product', 'purchase','base_suspend_security','eps_hr_employee','eps_notification_center','l10n_id_efaktur','account'],
    # 'external_dependencies': {
    #     'python': [
    #         'docx2pdf',
    #     ],
    # },
    'author':"ABK",
    'website':"",
    'category':"Koprol",
    'description':"""
Proposal
======
- Pengajuan proposal awal dari business unit berdasarkan kategori
- Nilai proposal belum final, namun merepresentasikan plafon
- Nilai total proposal subject to approval berdasarkan matrix di bisnis unit / division
    """,
    'data': [
        'views/eps_category.xml',
        'views/eps_proposal.xml',
        'report/report_eps_proposal.xml',
        'views/eps_initiatives_view.xml',
        'views/eps_quotation_view.xml',
        'views/product_view.xml',
        'views/eps_tender_view.xml',
        'views/res_partner_view.xml',
        'views/eps_koprol_setting_view.xml',
        'views/purchase_view.xml',
        'views/account_payment_term_view.xml',
        'views/res_bank_view.xml',
        'security/res_groups.xml',
        'data/scheduled_actions_data.xml'
        # 'security/ir.model.access.csv',
    ]
}