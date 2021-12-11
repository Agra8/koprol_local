{
    'name':"DMS MENU",
    'version':'1.0',
    'depends':['base','web_widget_many2many_tags_multi_selection','base_suspend_security'],
    'author':"TDM",
    'website':"http://www.honda-ku.com",
    'category':'Custom Modules',
    'description':"""DMS MENU""",
    'demo':[],
    'data':[
        # 'views/res_company_menu.xml',
        'views/dms_menu.xml',

        'security/res_groups.xml',
    ],
}