# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
            Override method for apply domain on user
        """
        context = dict(self.env.context)
        if context.get('category_id') and context.get('assign_to'):
            args.extend([('category_id', '=', context.get('category_id')),
                  ('equipment_assign_to', '=', context.get('assign_to'))])
            if context.get('assign_to') == 'employee':
                args.append(('employee_id', '=', False))
            elif context.get('assign_to') == 'department':
                args.append(('department_id', '=', False))
        return super(MaintenanceEquipment, self).name_search(name, args=args, operator=operator, limit=limit)