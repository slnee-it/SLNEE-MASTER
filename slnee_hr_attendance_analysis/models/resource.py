# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    tolerance_from = fields.Float('Tolerance from', size=8,
        help='Sign out done in the interval "Work to - Tolerance from" will be considered done at "Work to"')
    tolerance_to = fields.Float('Tolerance to', size=8,
        help='Sign in done in the interval "Work from + Tolerance to" will be considered done at "Work from"')


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    attendance_rounding = fields.Selection([
        ('60', '1'), ('30', '2'), ('20', '3'),
        ('12', '5'), ('10', '6'), ('7.5', '8'),
        ('6', '10'), ('5', '12'), ('4', '15'),
        ('3', '20'), ('2', '30'), ('1', '60'), ],
        'Attendance rounding', help='For instance, using rounding = 15 minutes, every sign in will be rounded to the following quarter hour and every sign out to the previous quarter hour')
    # 'attendance_rounding': fields.float('Attendance rounding', size=8,
        # help='For instance, using rounding = 15 minutes, every sign in will be rounded to the following quarter hour and every sign out to the previous quarter hour'),
    overtime_rounding = fields.Selection([
        ('60', '1'), ('30', '2'), ('20', '3'),
        ('12', '5'), ('10', '6'), ('7.5', '8'),
        ('6', '10'), ('5', '12'), ('4', '15'),
        ('3', '20'), ('2', '30'), ('1', '60'), ],
        'Overtime rounding', help='Setting rounding = 30 minutes, an overtime of 29 minutes will be considered as 0 minutes, 31 minutes as 30 minutes, 61 minutes as 1 hour and so on')
    overtime_rounding_tolerance = fields.Float('Overtime rounding tolerance', size=8,
        help='Overtime can be rounded using a tolerance. Using tolerance = 3 minutes and rounding = 15 minutes, if employee does overtime of 12 minutes, it will be considered as 15 minutes.')
    leave_rounding = fields.Selection([
        ('60', '1'), ('30', '2'), ('20', '3'),
        ('12', '5'), ('10', '6'), ('7.5', '8'),
        ('6', '10'), ('5', '12'), ('4', '15'),
        ('3', '20'), ('2', '30'), ('1', '60'), ],
        'Leave rounding', help='On the contrary of overtime rounding, using rounding = 15 minutes, a leave of 1 minute will be considered as 15 minutes, 16 minutes as 30 minutes and so on')
    overtime_type_ids = fields.One2many('resource.calendar.overtime.type', 'calendar_id', 'Overtime types')


class ResourceCalendarOvertimeRange(models.Model):
    _name = 'resource.calendar.overtime.type'
    _description = 'Overtime type'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Type Description', size=64, required=True)
    calendar_id = fields.Many2one('resource.calendar', 'Calendar')
    limit = fields.Float('Limit', size=8,
        help='Limit, in hours, of overtime that can be imputed to this type of overtime in a day. The surplus is imputed to the subsequent type')
