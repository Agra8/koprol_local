# -*- coding: utf-8 -*-
{
    'name': "Dms Branch",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': 'Tunas Honda',
	
    'website': "https://www.tunasgroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Utility",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','dms_area','base_suspend_security'],

    # always loaded
    'data': [
        "security/dms_res_branch_group.xml",
        "security/ir_rule.xml",
        "views/menu.xml",
        "views/dms_res_branch_view.xml",
        "views/dms_res_area_view.xml",
        "views/res_users_view.xml",
        "data/res_branch.xml",
		"data/res_area.xml",
		"security/ir.model.access.csv",
    ],
   	"installable": True,
	"auto_install": False,
	"application": True,
}
