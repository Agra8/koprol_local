{
    'name':"EPS - Proposal",
    'version':'10.0.1.0.0',
    'depends':['eps_menu', 'eps_config_files','eps_branch','eps_approval', 'mail'],
    'external_dependencies': {
        'python': [
            'docx2pdf',
        ],
    },
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
        'views/eps_initiatives_view.xml',
        'views/eps_quotation_view.xml',
        'security/res_groups.xml',
        # 'security/ir.model.access.csv',
    ]
}