# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta, time
import math
import calendar
import pytz


class wizard_calendar_report(models.TransientModel):
    _name = "attendance_analysis.wizard.calendar_report"

    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ], 'Month', default=lambda * a: str(datetime.now().month))
    year = fields.Integer('Year', default=lambda * a: datetime.now().year)
    from_date = fields.Date('From date', required=True, default=lambda * a: (datetime.now() - timedelta(30)).strftime('%Y-%m-%d'))
    to_date = fields.Date('To date', required=True, default=lambda * a: datetime.now().strftime('%Y-%m-%d'))
    employee_ids = fields.Many2many('hr.employee', 'calendar_report_employee_rel', 'employee_id', 'report_id', required=True, default=lambda s: s.env['hr.employee'].search([]))

    @api.onchange('month', 'year')
    def on_change_month(self):
        res = {}
        if self.year and self.month:
            month = int(self.month)
            day = calendar.monthrange(self.year, month)[1]
            to_date = date(self.year, month, day).strftime('%Y-%m-%d')
            res = {'value':{'to_date': to_date, 'from_date': date(self.year, month, 1).strftime('%Y-%m-%d')}}
        return res

    @api.multi
    def print_calendar(self):
        # active_tz = pytz.timezone(context.get("tz", "UTC") if context else "UTC")
        active_tz = self.env.context.get('tz', pytz.timezone('UTC'))
        def _get_attendance_date(attendance_date):
            # Convert in local timezone
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(active_tz)
            return datetime.strftime(attendance_date, '%Y-%m-%d %H:%M:%S')

        attendance_obj = self.env['hr.attendance']
        contract_obj = self.env['hr.contract']
        holidays_obj = self.env['hr.holidays']

        days_by_employee = {}

        form = self.read()[0]
        from_date = datetime.strptime(form['from_date'], '%Y-%m-%d')
        to_date = datetime.strptime(form['to_date'], '%Y-%m-%d')
        if from_date > to_date:
            raise UserError(_('From date must be < to date'))
        employee_ids = form['employee_ids']
        delta = to_date - from_date
        max_number_of_attendances_per_day = 0

        for employee_id in employee_ids:
            employee_id = str(employee_id)
            days_by_employee[employee_id] = {}
            day_count = 0
            while day_count < delta.days:
                current_date = from_date + timedelta(day_count)
                current_total_attendances = 0.0
                current_total_overtime = 0.0
                current_total_leaves = 0.0
                current_total_due = 24.0  # If contract is not specified: working days = 24/7
                current_total_inside_calendar = 0.0
                str_current_date = current_date.strftime('%Y-%m-%d')
                days_by_employee[employee_id][str_current_date] = {
                    'signin_1': '',
                    'signout_1': '',
                    'signin_2': '',
                    'signout_2': '',
                    'signin_3': '',
                    'signout_3': '',
                    'signin_4': '',
                    'signout_4': '',
                    }
                current_date_beginning = datetime.combine(current_date, time())
                str_current_date_beginning = current_date_beginning.strftime('%Y-%m-%d %H:%M:%S')
                current_date_end = datetime.combine(current_date, time()) + timedelta(1)
                str_current_date_end = current_date_end.strftime('%Y-%m-%d %H:%M:%S')

                attendance_ids = attendance_obj.search([
                    ('employee_id', '=', int(employee_id)),
                    ('check_in', '>=', str_current_date_beginning),
                    ('check_in', '<=', str_current_date_end),
                    # ('action', '=', 'sign_in'),
                    ])
                # computing attendance totals
                for attendance in attendance_obj.browse(attendance_ids):
                    current_total_attendances = attendance_obj.time_sum(current_total_attendances,
                        attendance.duration)
                    current_total_overtime = attendance_obj.time_sum(current_total_overtime,
                        attendance.outside_calendar_duration)
                    current_total_inside_calendar = attendance_obj.time_sum(current_total_inside_calendar,
                        attendance.inside_calendar_duration)

                if len(attendance_ids) < 5:
                    count = 1
                    for attendance in sorted(attendance_obj.browse(attendance_ids),
                        key=lambda x: x['check_in']):
                        if attendance.check_in and attendance.end_datetime:
                            days_by_employee[employee_id][str_current_date][
                                'signin_' + str(count)] = _get_attendance_date(attendance.check_in)[11:16]
                            days_by_employee[employee_id][str_current_date][
                                'signout_' + str(count)] = _get_attendance_date(attendance.end_datetime)[11:16]
                            count += 1
                    if len(attendance_ids) > max_number_of_attendances_per_day:
                        max_number_of_attendances_per_day = len(attendance_ids)

                days_by_employee[employee_id][str_current_date]['attendances'] = current_total_attendances
                days_by_employee[employee_id][str_current_date]['overtime'] = current_total_overtime

                active_contract_ids = self.env['hr.employee'].browse(int(employee_id)).get_active_contracts(date=str_current_date)
                # computing due total
                if active_contract_ids:
                    contract = contract_obj.browse(active_contract_ids[0])
                    if contract.working_hours and contract.working_hours.attendance_ids:
                        current_total_due = 0.0
                        for calendar_attendance in contract.working_hours.attendance_ids:
                            if (not calendar_attendance.dayofweek
                                or int(calendar_attendance.dayofweek) == current_date.weekday()) \
                                and (not calendar_attendance.date_from or
                                datetime.strptime(calendar_attendance.date_from, '%Y-%m-%d') <= current_date):
                                calendar_attendance_duration = attendance_obj.time_difference(
                                    calendar_attendance.hour_from, calendar_attendance.hour_to)
                                if calendar_attendance_duration < 0:
                                    raise UserError(_("%s: 'Work to' is < 'Work from'") % calendar_attendance.check_in)
                                current_total_due = attendance_obj.time_sum(current_total_due,
                                    calendar_attendance_duration)

                days_by_employee[employee_id][str_current_date]['due'] = current_total_due

                # computing leaves
                holidays_ids = holidays_obj.search([
                    '&',
                    '&',
                    '|',
                    # leave begins today
                    '&',
                    ('date_from', '>=', str_current_date_beginning),
                    ('date_from', '<=', str_current_date_end),
                    '|',
                    # leave ends today
                    '&',
                    ('date_to', '<=', str_current_date_end),
                    ('date_to', '>=', str_current_date_beginning),
                    # leave is ongoing
                    '&',
                    ('date_from', '<', str_current_date_beginning),
                    ('date_to', '>', str_current_date_end),
                    ('state', '=', 'validate'),
                    ('employee_id', '=', int(employee_id)),
                    ])
                for holiday in holidays_obj.browse(holidays_ids):
                    date_from = datetime.strptime(holiday.date_from, '%Y-%m-%d %H:%M:%S')
                    date_to = datetime.strptime(holiday.date_to, '%Y-%m-%d %H:%M:%S')
                    # if beginned before today
                    if date_from < current_date_beginning:
                        date_from = current_date_beginning
                    # if ends after today
                    if date_to > current_date_end:
                        date_to = current_date_end
                    current_total_leaves = attendance_obj.time_sum(current_total_leaves,
                        (date_to - date_from).total_seconds() / 60.0 / 60.0)

                days_by_employee[employee_id][str_current_date]['leaves'] = current_total_leaves
                if current_total_leaves > days_by_employee[employee_id][str_current_date]['due']:
                    days_by_employee[employee_id][str_current_date]['leaves'] = \
                        days_by_employee[employee_id][str_current_date]['due']
                due_minus_leaves = attendance_obj.time_difference(current_total_leaves, current_total_due)
                if due_minus_leaves < current_total_inside_calendar:
                    days_by_employee[employee_id][str_current_date]['negative'] = 0.0
                else:
                    days_by_employee[employee_id][str_current_date]['negative'] = \
                        attendance_obj.time_difference(current_total_inside_calendar, due_minus_leaves)

                if active_contract_ids:
                    contract = contract_obj.browse(active_contract_ids[0])
                    if contract.working_hours and contract.working_hours.leave_rounding:
                        float_rounding = float(contract.working_hours.leave_rounding)
                        days_by_employee[employee_id][str_current_date]['negative'] = math.floor(
                            days_by_employee[employee_id][str_current_date]['negative'] *
                            float_rounding) / float_rounding

                day_count += 1

        totals_by_employee = {}
        for employee_id in days_by_employee:
            totals_by_employee[employee_id] = {
                'total_attendances': 0.0,
                'total_overtime': 0.0,
                'total_negative': 0.0,
                'total_leaves': 0.0,
                'total_due': 0.0,
                'total_types': {},
            }

            for str_date in days_by_employee[employee_id]:
                totals_by_employee[employee_id]['total_attendances'] = attendance_obj.time_sum(
                    totals_by_employee[employee_id]['total_attendances'],
                    days_by_employee[employee_id][str_date]['attendances'])
                totals_by_employee[employee_id]['total_overtime'] = attendance_obj.time_sum(
                    totals_by_employee[employee_id]['total_overtime'],
                    days_by_employee[employee_id][str_date]['overtime'])
                totals_by_employee[employee_id]['total_negative'] = attendance_obj.time_sum(
                    totals_by_employee[employee_id]['total_negative'],
                    days_by_employee[employee_id][str_date]['negative'])
                totals_by_employee[employee_id]['total_leaves'] = attendance_obj.time_sum(
                    totals_by_employee[employee_id]['total_leaves'],
                    days_by_employee[employee_id][str_date]['leaves'])
                totals_by_employee[employee_id]['total_due'] = attendance_obj.time_sum(
                    totals_by_employee[employee_id]['total_due'],
                    days_by_employee[employee_id][str_date]['due'])

                # computing overtime types
                active_contract_ids = self.env['hr.employee'].browse(int(employee_id)).get_active_contracts(date=str_date)
                if active_contract_ids:
                    contract = contract_obj.browse(active_contract_ids[0])
                    if contract.working_hours and contract.working_hours.overtime_type_ids:
                        sorted_types = sorted(contract.working_hours.overtime_type_ids, key=lambda k: k.sequence)
                        current_overtime = days_by_employee[employee_id][str_date]['overtime']
                        for overtime_type in sorted_types:
                            if not totals_by_employee[employee_id]['total_types'].get(overtime_type.name, False):
                                totals_by_employee[employee_id]['total_types'][overtime_type.name] = 0.0
                            if current_overtime:
                                if current_overtime <= overtime_type.limit or not overtime_type.limit:
                                    totals_by_employee[employee_id]['total_types'][
                                        overtime_type.name] = attendance_obj.time_sum(totals_by_employee[
                                        employee_id]['total_types'][overtime_type.name], current_overtime)
                                    current_overtime = 0.0
                                else:
                                    totals_by_employee[employee_id]['total_types'][
                                        overtime_type.name] = attendance_obj.time_sum(totals_by_employee[
                                        employee_id]['total_types'][overtime_type.name], overtime_type.limit)
                                    current_overtime = attendance_obj.time_difference(overtime_type.limit,
                                        current_overtime)

                days_by_employee[employee_id][str_date]['attendances'] = attendance_obj.float_time_convert(
                    days_by_employee[employee_id][str_date]['attendances'])
                days_by_employee[employee_id][str_date]['overtime'] = attendance_obj.float_time_convert(
                    days_by_employee[employee_id][str_date]['overtime'])
                days_by_employee[employee_id][str_date]['negative'] = attendance_obj.float_time_convert(
                    days_by_employee[employee_id][str_date]['negative'])
                days_by_employee[employee_id][str_date]['leaves'] = attendance_obj.float_time_convert(
                    days_by_employee[employee_id][str_date]['leaves'])
                days_by_employee[employee_id][str_date]['due'] = attendance_obj.float_time_convert(
                    days_by_employee[employee_id][str_date]['due'])

            totals_by_employee[employee_id]['total_attendances'] = attendance_obj.float_time_convert(
                totals_by_employee[employee_id]['total_attendances'])
            totals_by_employee[employee_id]['total_overtime'] = attendance_obj.float_time_convert(
                totals_by_employee[employee_id]['total_overtime'])
            totals_by_employee[employee_id]['total_negative'] = attendance_obj.float_time_convert(
                totals_by_employee[employee_id]['total_negative'])
            totals_by_employee[employee_id]['total_leaves'] = attendance_obj.float_time_convert(
                totals_by_employee[employee_id]['total_leaves'])
            totals_by_employee[employee_id]['total_due'] = attendance_obj.float_time_convert(
                totals_by_employee[employee_id]['total_due'])

            for overtime_type in totals_by_employee[employee_id]['total_types']:
                totals_by_employee[employee_id]['total_types'][overtime_type] = attendance_obj.float_time_convert(totals_by_employee[employee_id]['total_types'][overtime_type])

        datas = {'ids': employee_ids}
        datas['model'] = 'hr.employee'
        datas['form'] = {}
        datas['form']['days_by_employee'] = days_by_employee
        datas['form']['totals_by_employee'] = totals_by_employee
        datas['form']['max_number_of_attendances_per_day'] = max_number_of_attendances_per_day

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'attendance_analysis.calendar_report',
            'datas': datas,
        }

wizard_calendar_report()
