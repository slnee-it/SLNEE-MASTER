# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import time
import math
from datetime import datetime, timedelta, date
from datetime import time as datetime_time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ResWeekdays(models.Model):
    _name = 'res.weekdays'

    code = fields.Integer('Code')
    name = fields.Selection([('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], 'Day')
    calendar_ids = fields.Many2many('resource.calendar', 'rel_weekdays_calendar', 'week_id', 'calendar_id', 'Calendars')


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    weekend_ids = fields.Many2many('res.weekdays', 'rel_weekdays_calendar', 'calendar_id', 'week_id', 'Weekends')


class LeaveDetail(models.Model):
    _name = "leave.detail"

    name = fields.Char(string="Month")
    period_id = fields.Many2one('year.period', string="Month")
    holiday_id = fields.Many2one('hr.holidays', string="Holiday")
    already_taken = fields.Float(string="Already Taken")
    already_taken_month = fields.Float(string="Already Taken in current Month")
    paid_leave = fields.Float(string="Paid Leave")
    unpaid_leave = fields.Float(string="Unpaid Leave")
    leave_hours = fields.Float(string="Paid Leave Hours")
    total_leave_hours = fields.Float(string="Total Leave Hours")
    unpaid_leave_hours = fields.Float(string="Unpaid Leave Hours")
    total_leave = fields.Float(string="Total Leave")


class Holidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def name_get(self):
        """
            Generate name and return,
            If record type add generate name string like, `name` + `holiday status name` + `fiscal year name`
            if record type remove generate name string like, `name` + `holiday status name`
        """
        res = []
        for record in self:
            name = ''
            if record.type == 'add':
                if record.employee_id:
                    name = name + record.employee_id.name + '-'
                if record.holiday_status_id:
                    name = name + record.holiday_status_id.name + '-'
                if record.fiscalyear:
                    name = name + record.fiscalyear.name
            if record.type == 'remove':
                if record.employee_id:
                    name = name + record.employee_id.name + '-'
                if record.holiday_status_id:
                    name = name + record.holiday_status_id.name
            res.append((record.id, name))
        return res

    @api.model
    def default_get(self, fields_data):
        """
            Default Get From Bonus line.
        """
        res = super(Holidays, self).default_get(fields_data)
        if res.get('date_from'):
            res.update({
                    'date_from': datetime.strptime(str(res['date_from']), DEFAULT_SERVER_DATETIME_FORMAT).strftime('%Y-%m-%d 02:30:00')
                })
        return res

    @api.constrains('date_from', 'number_of_days_temp')
    def validate_date(self):
        leaves = self.env['hr.holidays'].search([('id', '!=', self.id), ('employee_id', '=', self.employee_id.id), ('holiday_status_id.name', '=', 'Early Logout'), ('state', '=', 'validate')])
        for leave in leaves:
            if leave.date_from and self.date_from and self.holiday_status_id.name == 'Early Logout':
                if datetime.strptime(str(self.date_from),DEFAULT_SERVER_DATETIME_FORMAT).month == datetime.strptime(str(leave.date_from),"%Y-%m-%d %H:%M:%S").month:
                    raise ValidationError("you have not create Early Logout leave in same month.")
        if self.holiday_status_id.name == 'Early Logout' and self.number_of_days_temp > 0.5 or self.number_of_days_temp <= 0:
            raise ValidationError("The number of Days must be less than 0.5 and greater than 0.")

    @api.model
    def isWorkingDay(self, holiday_date, employee_id=False):
        """
            Check holiday date is working day
        """
        weekends = []
        if employee_id:
            contract = self.env['hr.employee'].browse(employee_id).get_active_contracts(holiday_date)
            if contract:
                working_hour = contract.resource_calendar_id
                if working_hour:
                    for contract_weekend in working_hour.weekend_ids:
                        weekends.append(contract_weekend.code)
        if datetime.strptime(holiday_date, DEFAULT_SERVER_DATETIME_FORMAT).isoweekday() in weekends:
            return False
        return True

    @api.model
    def isWeekendDay(self, holiday_date, employee_id=False):
        """
            Check holiday date is weekend day
        """
        weekends = []
        if employee_id:
            contract = self.env['hr.employee'].browse(employee_id).get_active_contracts(holiday_date)
            if contract:
                working_hour = contract.resource_calendar_id
                if working_hour:
                    for contract_weekend in working_hour.weekend_ids:
                        weekends.append(contract_weekend.code)
        if datetime.strptime(holiday_date, DEFAULT_SERVER_DATETIME_FORMAT).isoweekday() in weekends:
            return True
        return False

    @api.model
    def isPublicDay(self, holiday_date, employee_id=False, fiscalyear=False):
        """
            Check holiday date is public day
        """
        public_holi_obj = self.env['hr.holidays.public']
        year_obj = self.env['year.year']
        period_ids = self.fiscalyear.period_ids.search([('date_start','<=',datetime.today()),('date_stop','>=',datetime.today())])
        if period_ids:
            year = datetime.strptime(period_ids.date_start, DEFAULT_SERVER_DATE_FORMAT)
            if year:
                public_holi_line_obj = self.env['hr.holidays.public.line']
                public_holidays_ids = public_holi_obj.search([('year','=',year.year)])
                if public_holidays_ids:
                    holidays_line_ids = public_holi_line_obj.search([('year_id','=',public_holidays_ids[0].id)])
                    if holidays_line_ids:
                        for line_obj in holidays_line_ids:#public_holi_line_obj.browse(holidays_line_ids):
                            if (holiday_date >= line_obj.start_date + " 00:00:00" and holiday_date <= line_obj.end_date + " 23:59:59"):
                                return True
        return False

    @api.model
    def getWorkingDaysBetween(self , begin_date, end_date, number_of_days_temp, employee_id=False, fiscalyear=False, holiday_status_id=False):
        """
            Get the number of working days between begin_date and end_date inclusive
        """
        res = {'working_days': 0.0,
               'public_holiday_days': 0.0,
               'weekend_days': 0.0
               }
        begin_dt = datetime.strptime(begin_date, DEFAULT_SERVER_DATETIME_FORMAT)
        working_days = public_holiday_days = weekend_days = temp_days = 0.0
        while temp_days < number_of_days_temp:
            if self.isPublicDay(begin_dt.strftime('%Y-%m-%d %H:%M:%S'), employee_id, fiscalyear and fiscalyear.id or False):
                public_holiday_days += 1.0
            elif holiday_status_id and holiday_status_id.skip and self.isWeekendDay(begin_dt.strftime('%Y-%m-%d %H:%M:%S'), employee_id=employee_id):
                weekend_days += 1.0
            else:
                working_days += 1.0
            begin_dt += timedelta(days=1)
            temp_days += 1.0
        res.update({'working_days': working_days,
               'public_holiday_days': public_holiday_days,
               'weekend_days': weekend_days
               })
        return res

    @api.model
    def _get_default_year(self):
        """
            Get the default year
        """
        res = self.env['year.year'].find(time.strftime("%Y-%m-%d"), True)
        return res if res else False

    @api.one
    @api.depends('state', 'fiscalyear', 'employee_id', 'company_id', 'date_from', 'date_to', 'holiday_status_id', 'number_of_days_temp')
    def _carry_forward_check(self):
        """
            Check carry forward
        """
        self.carry_forward_check = False
        if self.type == 'remove':
            if self.fiscalyear.date_start:
                date_limit = datetime.strptime(self.fiscalyear.date_start, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=+3)
                date_limit = datetime.strftime(date_limit, '%Y-%m-%d')
                if self.date_from and (self.date_from >= self.fiscalyear.date_start and self.date_from <= date_limit):
                    self.carry_forward_check = True
                else:
                    today_date = time.strftime('%Y-%m-%d')
                    if today_date >= self.fiscalyear.date_start and today_date <= date_limit:
                        self.carry_forward_check = True

    fiscalyear = fields.Many2one('year.year', 'Year', readonly=True, states={'draft':[('readonly', False)], 'confirm':[('readonly', False)]}, default=_get_default_year)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=False, readonly=False, states={'done': [('readonly', True)]},
        default=lambda self: self.env.user.company_id)
    override_limit = fields.Float('Override Limit', digits=(3, 2), readonly=True, default=0.0, states={'draft':[('readonly', False)], 'confirm':[('readonly', False)]})
    carry_forward_limit = fields.Float('Carry Forward Limit', digits=(3, 2), readonly=True, default=0.0, states={'draft':[('readonly', False)], 'confirm':[('readonly', False)]})
    carry_forwarded = fields.Float(string='Previous Carry Forward', readonly=True, default=0.0, states={'draft':[('readonly', False)], 'confirm':[('readonly', False)]})

    limit = fields.Boolean('Limit')
    active = fields.Boolean('Active', default=True)
    carry_forward = fields.Boolean("Carry Forward")
    department_id = fields.Many2one('hr.department', 'Department')  # , related='employee_id.department_id'
    refuse_date = fields.Datetime('Refuse Date', readonly=True)
    refuse_uid = fields.Many2one('res.users', 'Refuse by', readonly=True)
    hr_validation = fields.Boolean(string='Apply HR Validation')  # ,related='holiday_status_id.hr_validation'
    hr_manager_id = fields.Many2one('hr.employee', 'HR Approval', readonly=True, help='This area is automaticly filled by the user who validate the leave with HR level (If Leave type need HR validation)')
    state = fields.Selection(selection_add=[('hr_validate', 'HR Approval')])
    carry_forward_check = fields.Boolean(compute='_carry_forward_check', string='Carry Forward Check', store=True)
    leave_details = fields.One2many('leave.detail', 'holiday_id', string="Leave Details", copy=False)

    @api.multi
    def _check_security_action_validate(self):
        if not (self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self._uid !=self.employee_id.parent_id.user_id.id or self._uid != self.employee_id.coach_id.user_id.id):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

    @api.multi
    def _check_security_action_approve(self):
        if not (self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self._uid != self.employee_id.parent_id.user_id.id or self._uid != self.employee_id.coach_id.user_id.id):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

    @api.multi
    def _check_security_action_refuse(self):
        if not (self.env.user.has_group(
                'hr_holidays.group_hr_holidays_user') or self._uid != self.employee_id.parent_id.user_id.id or self._uid != self.employee_id.coach_id.user_id.id):
            raise UserError(_('Only an HR Officer or Manager can refuse leave requests.'))

    @api.multi
    def action_refuse(self):
        self._check_security_action_refuse()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1', 'hr_validate']:
                raise UserError(_('Leave request must be confirmed or validated in order to refuse it.'))

            if holiday.state == 'validate1':
                holiday.write({'state': 'refuse', 'first_approver_id': current_employee.id, 'refuse_uid': self.env.uid, 'refuse_date': fields.Datetime.now()})
            else:
                holiday.write({'state': 'refuse', 'second_approver_id': current_employee.id, 'refuse_uid': self.env.uid, 'refuse_date': fields.Datetime.now()})
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        self._remove_resource_leave()
        return True

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state in ['confirm', 'validate', 'validate1', 'hr_validate']:
                raise UserError(_('You cannot delete a leave which is in %s state.') % (rec.state))
        return super(Holidays, self).unlink()

    @api.multi
    def calculate_leave_details(self):
        self.leave_details.unlink()
        contract_ids = self.env['hr.payslip'].get_contract(self.employee_id, self.fiscalyear.date_start, self.fiscalyear.date_stop)
        contract_ids = self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.resource_calendar_id)
        resource_calendar_id = contract_ids and contract_ids[0].resource_calendar_id or self.employee_id.resource_calendar_id
        if self.type == 'remove' and resource_calendar_id:
            day_from = datetime.combine(fields.Date.from_string(self.date_from), datetime_time.min)
            day_to = datetime.combine(fields.Date.from_string(self.date_to), datetime_time.max)
            leave_day_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            leave_day_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATETIME_FORMAT)
            nb_of_days = (day_to - day_from).days + 1
            period_dict = {}
            for day in range(0, nb_of_days):
                leave_date = (day_from + timedelta(days=day))
                leave_day_counter = 1.0
                period_id = self.fiscalyear.period_ids.filtered(lambda l: datetime.strptime(l.date_start, DEFAULT_SERVER_DATE_FORMAT).date() <= leave_date.date() and datetime.strptime(l.date_stop, DEFAULT_SERVER_DATE_FORMAT).date() >= leave_date.date())
                if period_id:
                    if self.holiday_status_id.skip:
                        is_working_day = self.isWorkingDay(str(leave_date), employee_id=self.employee_id.id)
                        if not is_working_day:
                            continue
                    if leave_day_from.date() == leave_date.date():
                        leave_start_time = self.employee_id.get_start_work_hour(leave_day_from.date(), resource_calendar_id)
                        if leave_start_time and leave_day_from > leave_start_time:
                            leave_day_counter = 0.5
                    if leave_day_to.date() == leave_date.date():
                        leave_end_time = self.employee_id.get_end_work_hour(leave_day_to.date(), resource_calendar_id)
                        if leave_end_time and leave_day_to < leave_end_time:
                            leave_day_counter = 0.5
                    work_hours = self.employee_id.get_day_work_hours_count(leave_date.date(), calendar=resource_calendar_id)
                    if not work_hours:
                        work_hours = 0.0
                    if period_id.id in period_dict:
                        period_dict.update({period_id.id: [period_dict.get(period_id.id)[0] + leave_day_counter, period_dict.get(period_id.id)[1] + work_hours]})
                    else:
                        period_dict.update({period_id.id: [leave_day_counter, work_hours]})
            for period_id, leave_day in period_dict.items():
                period_id = self.env['year.period'].browse(period_id)
                leave_days = []
                day_from = datetime.strptime(period_id.date_start, DEFAULT_SERVER_DATE_FORMAT)
                day_to = datetime.strptime(period_id.date_stop, DEFAULT_SERVER_DATE_FORMAT)
                nb_of_days = (day_to - day_from).days + 1
                for day in range(0, nb_of_days):
                    day_from_start = datetime.strptime(((day_from + timedelta(days=day)).strftime("%Y-%m-%d 00:00:00")), DEFAULT_SERVER_DATETIME_FORMAT)
                    day_from_end = datetime.strptime(((day_from + timedelta(days=day)).strftime("%Y-%m-%d 23:59:59")), DEFAULT_SERVER_DATETIME_FORMAT)
                    day_intervals = resource_calendar_id._get_leave_intervals(resource_id=self.employee_id.resource_id.id, start_datetime=day_from_start, end_datetime=day_from_end)
                    for interval in day_intervals:
                        holiday = interval[2]['leaves'].holiday_id
                        if holiday.holiday_status_id.id == self.holiday_status_id.id:
                            if holiday.holiday_status_id.skip:
                                continue
                            leave_time = (interval[1] - interval[0]).seconds / 3600
                            leave_days.append(1.0 if leave_time > 4.0 else 0.5)
                day_leave_intervals = self.employee_id.iter_leaves(day_from, day_to + timedelta(days=1), calendar=resource_calendar_id)
                for day_intervals in day_leave_intervals:
                    for interval in day_intervals:
                        holiday = interval[2]['leaves'].holiday_id
                        if holiday.holiday_status_id.id == self.holiday_status_id.id:
                            if holiday.holiday_status_id.skip:
                                leave_time = (interval[1] - interval[0]).seconds / 3600
                                work_hours = self.employee_id.get_day_work_hours_count(interval[0].date(), calendar=resource_calendar_id)
                                if work_hours:
                                    leave_days.append(leave_time / work_hours)
                paid_leaves = leave_day[0]
                leave_hours = leave_day[1]
                unpaid_leave_hours = leave_day[1]
                total_leave_hours = leave_day[1]
                unpaid_leave = 0.0
                if self.holiday_status_id.is_deduction and self.holiday_status_id.deduction_by:
                    total_leave_day = self.holiday_status_id.leaves_taken + leave_day[0]
                    if self.holiday_status_id.deduction_by == 'day':
                        rule_line = self.holiday_status_id.rule_ids.filtered(lambda l: float(l.limit_from) <= float(total_leave_day) and float(l.limit_to) >= float(total_leave_day))
                        if rule_line:
                            paid_leaves = float(float(paid_leaves * rule_line[0].limit_per) / 100)
                            leave_hours = float(float(leave_hours * rule_line[0].limit_per) / 100)
                    elif self.holiday_status_id.deduction_by == 'year':
                        year_start_date = date(date.today().year, 1, 1)
                        year_end_date = date(date.today().year, 12, 31) + timedelta(days=1)
                        year_days = year_end_date - year_start_date
                        year_days = float(total_leave_day / year_days.days)
                        rule_line = self.holiday_status_id.rule_ids.filtered(lambda l: float(l.limit_from) <= float(year_days) and float(l.limit_to) >= float(year_days))
                        if rule_line:
                            paid_leaves = float(float(paid_leaves * rule_line[0].limit_per) / 100)
                            leave_hours = float(float(leave_hours * rule_line[0].limit_per) / 100)
                unpaid_leave_hours = leave_day[1] - leave_hours
                unpaid_leave = (leave_day[0] - paid_leaves)
                leave_detail_id = self.env['leave.detail'].create({
                        'holiday_id': self.id,
                        'name': period_id.name,
                        'already_taken_month': sum(leave_days),
                        'already_taken': self.holiday_status_id.leaves_taken,
                        'paid_leave': paid_leaves,
                        'unpaid_leave': unpaid_leave,
                        'total_leave': leave_day[0],
                        'leave_hours': leave_hours,
                        'unpaid_leave_hours': unpaid_leave_hours,
                        'total_leave_hours': total_leave_hours,
                        'period_id': period_id.id
                    })

    @api.model
    def create(self, vals):
        """
            create a new record
        """
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id})
        if vals.get('type') == 'add' and vals.get('holiday_status_id'):
            holiday_status = self.env['hr.holidays.status'].browse(vals['holiday_status_id'])
            if holiday_status.one_time_usable:
                leave_request_ids = self.search_count([('employee_id', '=', vals.get('employee_id', False)),
                                                 ('holiday_status_id', '=', holiday_status.id),
                                                ('type', '=', 'remove'), ('state', '=', 'validate')])
                if leave_request_ids:
                    raise UserError(_('You can not allocate this leave to this employee'))
        res = super(Holidays, self).create(vals)
        if res.type == 'remove':
            res.calculate_leave_details()
        return res

    @api.multi
    def write(self, vals):
        """
            update existing record
        """
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id})
        if vals.get('type') == 'add' or vals.get('holiday_status_id') or vals.get('employee_id'):
            holiday_status_id = vals.get('holiday_status_id', self.holiday_status_id.id)
            employee_id = vals.get('employee_id', self.employee_id.id)
            holiday_status = self.env['hr.holidays.status'].browse(holiday_status_id)
            if holiday_status.one_time_usable:
                leave_request_ids = self.search_count([('employee_id', '=', employee_id),
                                                        ('holiday_status_id', '=', holiday_status_id),
                                                        ('type', '=', 'remove'), ('state', '=', 'validate')])
                if leave_request_ids:
                    raise UserError(_('You can not allocate this leave to this employee'))
        res = super(Holidays, self).write(vals)
        for obj in self:
            if obj.type == 'remove' and (vals.get('date_from') or vals.get('date_to') or vals.get('holiday_status_id') or vals.get('employee_id') or vals.get('number_of_days_temp')):
                obj.calculate_leave_details()
        return res

    @api.onchange('date_from', 'date_to')
    def onchange_holidays(self):
        """
            Check date from, date to is it holidays
        """
        result = {'value': {}}
        if not self.date_from:
            return result
        if not self.fiscalyear:
            self.date_from = False
            raise UserError(_('Please define the Public Holiday Year for this leave'))
        if self.date_from:
            if self.date_from > self.fiscalyear.date_stop + " 23:59:59" or self.date_from < self.fiscalyear.date_start + " 00:00:00":
                raise UserError(_('Effective date must be between %s and %s') % (self.fiscalyear.date_start + " 00:00:00", self.fiscalyear.date_stop + " 23:59:59"))
            # effective_date = datetime.strptime(effective_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')#00:00:00
            # Fixed for Saudi Company
            # self.date_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT).strftime('%Y-%m-%d 02:30:00')  # 00:00:00
            if not self.date_to:
                # Fixed for Saudi Company
                self.date_to = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT).strftime('%Y-%m-%d 18:00:00')
            self._onchange_date_from()
            working_days_dict = self.getWorkingDaysBetween(self.date_from, self.date_to, self.number_of_days_temp, self.employee_id.id, self.fiscalyear, self.holiday_status_id)
            self.number_of_days_temp = working_days_dict['working_days']

    @api.onchange('date_to')
    # date_from, date_to, number_of_days_temp, fiscalyear=False, employee_id=False,holiday_status_id=False
    def onchange_end_date(self):
        """
            onchange end date, check the no of working days
        """
        result = {}
        if not self.date_to:
            return result
        if not self.date_from:
            return result
        if (self.date_from and self.date_to) and (self.date_from > self.date_to):
            raise UserError(_('The start date must be anterior to the end date.'))
        if not self.fiscalyear:
            raise UserError(_('Please Define the Public Holiday Year for this leave'))
        if self.date_to > self.fiscalyear.date_stop + " 23:59:59" or self.date_to < self.fiscalyear.date_start + " 00:00:00":
            raise UserError(_('End Date must be between %s and %s') % (self.fiscalyear.date_start + " 00:00:00", self.fiscalyear.date_stop + " 23:59:59"))

        # number_of_days_temp = self._onchange_date_to(self.date_to, self.date_from)['value']['number_of_days_temp']
        self._onchange_date_to()
        working_days_dict = self.getWorkingDaysBetween(self.date_from, self.date_to, self.number_of_days_temp, self.employee_id.id, self.fiscalyear, self.holiday_status_id)
        self.number_of_days_temp = working_days_dict['working_days']
        self.no_of_days = working_days_dict['working_days']

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        super(Holidays, self)._onchange_employee_id()

    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        """
            change the details of limit, carry forward if type is add,
            change the details of hr validation if type is remove
        """
        self.carry_forward = False
        self.limit = False
        self.hr_validation = False
        if self.type == 'add' and self.holiday_status_id:
            if self.holiday_status_id.carry_forward:
                self.carry_forward = True
            if self.holiday_status_id.limit:
                self.limit = True
        if self.type == 'remove' and self.holiday_status_id:
            if self.holiday_status_id.hr_validation:
                self.hr_validation = True
        self.onchange_holidays()
        self.onchange_end_date()

    @api.onchange('company_id', 'fiscalyear')
    def onchange_company_id(self):
        """
            check the company depends on fiscal year
        """
        res = {'domain':{}}
        if self.company_id and not self.fiscalyear:
            self.fiscalyear = False
            res['domain'].update({'fiscalyear': [('company_id', '=', self.company_id.id)]})
        elif self.fiscalyear and self.company_id:
            self.company_id = self.fiscalyear.company_id and self.fiscalyear.company_id.id or False
        return res

    @api.onchange('holiday_status_id', 'fiscalyear')
    def onchange_carryforward(self):
        self.carry_forwarded = 0.0
        if self.holiday_status_id and self.fiscalyear:
            previous_year = self.env['year.year'].find(str(datetime.now().date() - relativedelta(years=1)), True, True)
            if previous_year:
                alloc_ids = self.search([('type', '=', 'add'), ('state', '=', 'validate'), ('employee_id', '=', self.employee_id.id),
                                                      ('holiday_status_id', '=', self.holiday_status_id.id), ('fiscalyear', '=', previous_year.id)])

                if alloc_ids:
                    leaves_rest = alloc_ids.holiday_status_id.get_days(alloc_ids.employee_id.id, previous_year.id)[alloc_ids.holiday_status_id.id]['remaining_leaves']
                    leaves_rest = ((leaves_rest > 0) and leaves_rest) or 0
                    limit_days = (leaves_rest > alloc_ids.carry_forward_limit and alloc_ids.carry_forward_limit) or leaves_rest
                    self.carry_forwarded = limit_days or 0.0

    @api.constrains('state', 'number_of_days_temp', 'holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            if holiday.holiday_type == 'employee' and holiday.type == 'remove' and holiday.state not in ['hr_validate','validate']:  # and record.state != 'draft':
                all_details = holiday.holiday_status_id.get_days(holiday.employee_id.id, holiday.fiscalyear and holiday.fiscalyear.id or False)[holiday.holiday_status_id.id]
                leaves_rest = all_details['remaining_leaves']
                carry_forward_leave = all_details['carry_forward_leaves']
                max_leaves = all_details['max_leaves']
                if holiday.holiday_status_id.carry_forward and holiday.fiscalyear and holiday.fiscalyear.date_start:
                    date_limit = datetime.strptime(holiday.fiscalyear.date_start, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=+3, days=-1)
                    end_date = date_limit.strftime('%Y-%m-%d 23:59:59')
                    context = dict(self.env.context)
                    context.update({'end_date':end_date})
                    leaves_details = self.with_context(context).holiday_status_id.get_days(holiday.employee_id.id, holiday.fiscalyear and holiday.fiscalyear.id or False)
                    leaves_taken = leaves_details[holiday.holiday_status_id.id]['leaves_taken']
                    if carry_forward_leave:
                        if holiday.carry_forward_check:
                            total_leaves = max_leaves + carry_forward_leave
                            leaves_rest = total_leaves - leaves_taken
                        else:
                            c_f_leave = 0.0
                            if leaves_taken >= carry_forward_leave:
                                c_f_leave = carry_forward_leave
                            else:
                                c_f_leave = carry_forward_leave - leaves_taken
                            leaves_rest += c_f_leave
                    if leaves_rest < holiday.number_of_days_temp:
                        raise UserError(_('There are not enough %s allocated for employee %s; please contact your HR People for this leave type.') % (holiday.holiday_status_id.name, holiday.employee_id.name))
                if leaves_rest < holiday.number_of_days_temp and not holiday.holiday_status_id.limit:
                    raise UserError(_('There are not enough %s allocated for employee %s; please contact your HR People for this leave type.') % (holiday.holiday_status_id.name, holiday.employee_id.name))
                elif holiday.limit and holiday.override_limit > 0.0:
                    if leaves_rest < holiday.number_of_days_temp:
                        raise UserError(_('There are not enough %s remaining leaves for employee %s; please contact your HR People for this leave type.') % (holiday.holiday_status_id.name, holiday.employee_id.name))
            return True

    @api.multi
    def action_draft(self):
        """
            holiday reset state
        """
        for holiday in self:
            holiday.hr_manager_id = False
            holiday.refuse_uid = False
            holiday.refuse_date = False
        super(Holidays, self).action_draft()

    @api.multi
    def action_validate(self):
        return super(Holidays, self).action_validate()


    @api.multi
    def holidays_hr_validate_notificate(self):
        """
            sent a notification to the user
        """
        for obj in self:
            obj.message_post(_("Request approved, waiting hr validation."))
