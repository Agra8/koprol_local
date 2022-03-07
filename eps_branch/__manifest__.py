{
    'name':"EPS - Branch",
    'version':'10.0.1.0.0',
    'depends':['eps_menu', 'eps_localization', 'hr'],
    'author':"EPS",
    'category':"KOPROL",
    'description':"""
Branch
======
- Add functionality 1 comapany for multiple branches
    """,
    'data': [
        'views/res_branch_views.xml',
        'views/res_area_views.xml',
        'views/res_users_views.xml',
        'views/res_company_views.xml',
        'views/eps_divisi_views.xml',
        'views/eps_business_views.xml',
        'security/ir_rule.xml',
        'security/res_group.xml',
        'security/ir.model.access.csv',

    ],
    'external_dependencies': {
        'python': ['validate_email','pytz']
    },
}