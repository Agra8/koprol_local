# -*- coding: utf-8 -*-
{
    'name': "eps_job",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    "author": "Tunas Honda",
    'website': "https://www.tunasgroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Utility",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','eps_branch','eps_department'],

    # always loaded
    'data': [
      	"security/ir.model.access.csv",
		"security/res_groups.xml",
		"views/menu.xml",
		"views/hr_job_view.xml",
		"views/hr_job_mapping_view.xml",
		"data/res_groups_job_category.xml",
		"data/res_groups_job.xml",
  		"data/hr_job_data.xml",
    ],
  	"installable": True,
	"auto_install": False,
	"application": True,
}
