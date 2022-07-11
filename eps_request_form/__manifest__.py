# -*- coding: utf-8 -*-
{
    'name': "Request Form",

    'summary': """
        in this module you can create, view and edit JRF / ARF Data and the request came from website ARF / JRF.
        don't forget to check what module depends on. """,

    'description': """
        The module is Backend for JRF / ARF Online.
    """,

    'author': "Tunas Honda",
    'website': "http://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','email_template_qweb','eps_branch','eps_hr_employee', 'eps_teams', 'eps_menu', 'eps_department', 'hr'],

    # always loaded
    'data': [
        
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/menu.xml',
        'views/eps_request_form_view.xml',
        'views/eps_master_jrf_arf_view.xml',
        'views/eps_master_jrf_arf_kategori_view.xml',
        'views/eps_request_form_line_view.xml',
        
        # 'data/data_master_arf_jrf.xml',
        'data/ir_ui_view.xml',
        'data/mail_template.xml',

        'report/eps_request_form_report_wizard.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
