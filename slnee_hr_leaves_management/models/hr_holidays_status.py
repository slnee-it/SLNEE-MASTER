# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from itertools import groupby
from operator import itemgetter



class LeaveRuleLine(models.Model):
    _name = "hr.leave.rule.line"

    name = fields.Char(string="Name", required=True, copy=False)
    limit_from = fields.Integer(string="Limit From", required=True, copy=False)
    limit_to = fields.Integer(string="Limit To", copy=False)
    limit_per = fields.Integer(string="Limit(%)", required=True, copy=False)
    holiday_status_id = fields.Many2one('hr.holidays.status', string="Leave Type", copy=False)

    @api.multi
    @api.constrains('limit_from', 'limit_to')
    def _check_days(self):
        for rule_id in self:
            if rule_id.limit_from > rule_id.limit_to:
                raise ValidationError(_("'Limit To' should be greater than 'Limit From'!"))
            line_ids = self.search([('limit_from', '<=', rule_id.limit_to), ('limit_to', '>=',
             rule_id.limit_from), ('holiday_status_id', '=', rule_id.holiday_status_id.id),
            ('id', '<>', rule_id.id)])
            if line_ids:
                raise ValidationError(_('Two (2) Rule Lines for leave are overlapping!'))


class HolidaysType(models.Model):
    _inherit = "hr.holidays.status"

    @api.multi
    def _compute_leaves(self):
        data_days = {}
        if 'employee_id' in self._context:
            employee_id = self._context['employee_id']
        else:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).id

        if employee_id:
            data_days = self.get_days(employee_id)

        for holiday_status in self:
            result = data_days.get(holiday_status.id, {})
            holiday_status.max_leaves = result.get('max_leaves', 0)
            holiday_status.leaves_taken = result.get('leaves_taken', 0)
            holiday_status.remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)
            holiday_status.carry_forward_leaves = result.get('carry_forward_leaves', 0)

    carry_forward = fields.Boolean('Allow to Carry Forward', default=False)
    is_deduction = fields.Boolean(string="Leave Deduction", default=False)
    skip = fields.Boolean('Allow to Skip', help="Allow to skip in Weekends", default=False)
    sick_leave = fields.Boolean('Sick Leave', default=False)
    code = fields.Char(string="Code")
    hr_validation = fields.Boolean('Apply HR Validation', help="When selected, the Allocation/Leave Requests for this type require a hr validation to be approved.", default=False)
    one_time_usable = fields.Boolean('One Time Used', default=False)
    maternity_leave = fields.Boolean('Maternity Leave', default=False)
    # carry forward leaves
    max_leaves = fields.Float(compute='_compute_leaves', string='Maximum Allowed', help='This value is given by the sum of all holidays requests with a positive value.')
    leaves_taken = fields.Float(compute='_compute_leaves', string='Leaves Already Taken', help='This value is given by the sum of all holidays requests with a negative value.')
    remaining_leaves = fields.Float(compute='_compute_leaves', string='Remaining Leaves', help='Maximum Leaves Allowed - Leaves Already Taken')
    carry_forward_leaves = fields.Float(compute='_compute_leaves', string='Remaining Leaves', help='Maximum Leaves Allowed - Leaves Already Taken')
    virtual_remaining_leaves = fields.Float(compute='_compute_leaves', string='Virtual Remaining Leaves', help='Maximum Leaves Allowed - Leaves Already Taken - Leaves Waiting Approval')
    rule_ids = fields.One2many('hr.leave.rule.line', 'holiday_status_id', string="Rules")
    deduction_by = fields.Selection([('day', 'Days'), ('year', 'Year')], string="Deduction By")

    @api.constrains('carry_forward')
    def _check_carry_forward(self):
        self.ensure_one()
        holiday_status_ids = self.search([('carry_forward', '=', True)])
        if len(holiday_status_ids) > 1:
            return ValidationError('You can not have 2 leaves which can be defined as carry forward!')

    @api.multi
    def get_days(self, employee_id, fiscalyear=False):
        # need to use `dict` constructor to create a dict per id
        result = dict((id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0, carry_forward_leaves=0, override_limit=0)) for id in self.ids)
        context = dict(self.env.context)
        domain = [
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids),
        ]
        if fiscalyear or context.get('fiscalyear'):
            domain.append(('fiscalyear', '=', fiscalyear or context.get('fiscalyear')))
        holidays = self.env['hr.holidays'].search(domain)

        for holiday in holidays:
            status_dict = result[holiday.holiday_status_id.id]
            if holiday.type == 'add':
                if holiday.state == 'validate':
                    # note: add only validated allocation even for the virtual
                    # count; otherwise pending then refused allocation allow
                    # the employee to create more leaves than possible
                    status_dict['virtual_remaining_leaves'] += holiday.number_of_days_temp
                    status_dict['remaining_leaves'] += holiday.number_of_days_temp
                    status_dict['carry_forward_leaves'] = 0.0
                    if holiday.carry_forward:
                        status_dict['max_leaves'] += holiday.number_of_days_temp + holiday.override_limit
                        status_dict['carry_forward_leaves'] += holiday.carry_forwarded
                    elif holiday.limit:
                        status_dict['max_leaves'] += holiday.number_of_days_temp + holiday.override_limit
                    else:
                        status_dict['max_leaves'] += holiday.number_of_days_temp
            elif holiday.type == 'remove':  # number of days is negative
                status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
                if holiday.state == 'validate':
                    status_dict['leaves_taken'] += holiday.number_of_days_temp
                    status_dict['remaining_leaves'] -= holiday.number_of_days_temp
        return result

    @api.multi
    def name_get(self):
        if not self._context.get('employee_id', False):
            # leave counts is based on empoyee_id, would be inaccurate if not based on correct employee
            return super(HolidaysType, self).name_get()
        res = []
        for record in self:
            name = record.name
            if not record.limit:
                if record.carry_forward:
                    name = name + ('  (%d remaining out of %d + %d)' % (record.max_leaves - record.leaves_taken or 0.0, record.max_leaves or 0.0, record.carry_forward_leaves or 0.0))
                else:
                    name = name + ('  (%d remaining out of %d)' % (record.max_leaves - record.leaves_taken or 0.0, record.max_leaves or 0.0))
            res.append((record.id, name))
        return res


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_remaining_leaves(self):
        """ Helper to compute the remaining leaves for the current employees
            :returns dict where the key is the employee id, and the value is the remain leaves
        """
        self._cr.execute("""
            SELECT
                sum(h.number_of_days) AS days,
                h.employee_id
            FROM
                hr_holidays h
                join hr_holidays_status s ON (s.id=h.holiday_status_id)
            WHERE
                h.state='validate' AND
                s.carry_forward=True AND
                h.employee_id in %s
            GROUP BY h.employee_id""", (tuple(self.ids),))
        return dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())
