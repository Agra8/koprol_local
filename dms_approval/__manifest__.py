# -*- coding: utf-8 -*-
{
    'name': "dms_approval",

    'summary': """
        Master Approval""",

    'description': """
        Master Approval
    """,

    'author': "Tunas Honda",
    'website': "http://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/dms_approval_config_view.xml',
        'views/dms_approval_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
