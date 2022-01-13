{
    'name':"DMS CONF SAVED IMAGES",
    'version':'10.0.1.0.0',
    'depends':['dms_menu'],
    'author':"TDM",
    'website':"www.honda-ku.com",
    'category':"DMS",
    'description':"""DMS CONF SAVED IMAGES""",
    'data': [
        'security/res_groups.xml',
        'views/dms_config_image.xml',
        'security/ir.model.access.csv',
    ],
    'external_dependencies' : {
        'python' : ['pysftp'],
    }
}