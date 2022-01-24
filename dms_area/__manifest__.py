# -*- coding: utf-8 -*-
{
    'name': "dms_area",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    "author": "Tunas Honda",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Utility",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','dms_menu'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
		"security/dms_res_area_group.xml",
		"views/dms_res_area_view.xml",
		"security/ir.model.access.csv",
    ],
    # only loaded in demonstration mode
	"installable": True,
	"auto_install": False,
	"application": True,
}
