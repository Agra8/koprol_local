{
    "name":"EPS B2b Portal",
    "version":"0.1",
    "author":"EPS",
    "website":"",
    "category":"EPS",
    "description": """
        EPS Portal API
    """,
    "depends":["eps_menu","base"],
    "init_xml":[],
    "demo_xml":[],
    "data":[
        
        'views/eps_menu.xml',
        'views/res_users.xml',
        'views/eps_b2b_portal_client_view.xml',
        'views/eps_api_log_view.xml',
        'views/eps_b2b_api_configuration_view.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
    ],
    "active":False,
    "installable":True,
}
