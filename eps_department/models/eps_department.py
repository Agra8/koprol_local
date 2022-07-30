#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib


# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import Warning,ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class HrDepartment(models.Model):
    _inherit = "hr.department"

    # 7: defaults methods

    # 8: fields
    code = fields.Char(string='Department Code')

    # 8: relation fields

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    def _update_employee_manager(self, manager_id):
        employees = self.env['hr.employee']
        for department in self:
            employees = employees | self.env['hr.employee'].search([
                ('id', '!=', manager_id),
                ('department_id', '=', department.id),
                ('parent_id', '=', department.manager_id.id)
            ])
        
        update_data = {'parent_id': manager_id}
        for employee in employees:
            employee.write(update_data)



    # 11: override methods