# -*- coding: utf-8 -*-
{
    'name': "dms_report",

    'summary': """
        create report with query result
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Liong",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
