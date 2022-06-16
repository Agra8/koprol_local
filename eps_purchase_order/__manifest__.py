{
    'name':"EPS - Purchase Order",
    'version':'10.0.1.0.0',
    'depends':['purchase'],
    # 'external_dependencies': {
    #     'python': [
    #         'docx2pdf',
    #     ],
    # },
    'author':"ELEOS",
    'website':"",
    'category':"Koprol",
    'description':"""
EPS Purchase
======
- Custom Print RFQ
    """,
    'data': [
        'views/eps_purchase_order.xml',
        'report/report_eps_print_po.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv'
    ]
}