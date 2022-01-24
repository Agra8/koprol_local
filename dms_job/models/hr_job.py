#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Job(models.Model):
    _inherit = "hr.job"
    _description = "Job"

    # 7: defaults methods

    # 8: fields
    sales_force = fields.Selection(selection=[('salesman','Salesman'),('sales_koordinator','Sales Koordinator'),('soh','SOH'),('am','Area Manager'),('mechanic','Mechanic')],  string="Sales force",  help="")
    sales_category = fields.Selection(string="Kategori Insentif", selection=[('sales_partner','Sales Partner'),('sales_counter','Sales Counter'),('sales_payroll','Sales Payroll'),('sales_koordinator','Sales Coordinator'),('sales_digital','Sales Digital')])
    kategori = fields.Selection(selection=[('md','MD'),('dealer','Dealer'),('ho','Head Office')],  string="Kategori",  help="")
    job_level = fields.Selection(selection=[('1','Clerk'),('2','Staff'),('3','Supervisor'),('4','Manager'),('5','OM / GM / SM') ,('6','CHIEF / VICE PRESIDENT')],  string="Level",  help="")

    # 9: relation fields
    group_id = fields.Many2one(comodel_name='res.groups',  string='Group',  help='')