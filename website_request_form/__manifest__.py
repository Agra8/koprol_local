# -*- coding: utf-8 -*-
{
    'name': "website_request_form",

    'summary': """
        Request Form for JRF / ARF in any website""",

    'description': """
        Request Form for JRF / ARF in any website
    """,

    'author': "TDM",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/assets.xml',
        'views/assetsjs.xml',
        'views/menu.xml',
        'views/website_request_form.xml',
        'views/website_request_form_done.xml',
        'views/website_request_form_status.xml',
        'views/website_request_form_approval.xml',
        'views/notfound.xml',
        'views/website_request_form_reject.xml',
        'views/sorry_page.xml',
        'views/thank_you_reject.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
