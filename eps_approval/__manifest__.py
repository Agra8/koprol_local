{
    "name":"EPS Approval",
    "version":"1.0",
    "author":"EPS",
    "website":"",
    "category":"EPS",
    "description": """
        Approval for EPS
    """,
    "depends":["eps_menu","eps_branch","base_suspend_security"],
    "init_xml":[],
    "demo_xml":[],
    "data":[
            "views/eps_approval_view.xml",
            'security/ir.model.access.csv',
            'security/res_groups.xml',
            'data/scheduled_action.xml'
              ],
    "active":False,
    "installable":True
}