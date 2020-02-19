# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import math
from odoo.tools import pycompat, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
import pytz
from datetime import datetime, timedelta


class ResCompany(models.Model):
    _inherit = 'res.company'

    working_time_precision = fields.Float('Working Time Precision', help='The precision used to analysis working times over working schedule', required=False, default=0.016666667)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def float_time_convert(self, float_val):
        '''
            Convert float value into time.
        '''
        hours = math.floor(abs(float_val))
        mins = abs(float_val) - hours
        mins = round(mins * 60)
        if mins >= 60.0:
            hours = hours + 1
            mins = 0.0
        float_time = '%02d:%02d' % (hours, mins)
        return float_time

    def time_difference(self, float_start_time, float_end_time):
        """
            Calculate difference between start and end time
        """
        delta = timedelta(hours=(float_end_time - float_start_time))
        return delta.total_seconds() / 60.0 / 60.0

    def time_sum(self, float_first_time, float_second_time):
        """
            Addition of first and second time
        """
        first_timedelta = timedelta(hours=float_first_time)
        second_timedelta = timedelta(hours=float_second_time)
        return (first_timedelta + second_timedelta).total_seconds() / 60.0 / 60.0

    def _split_norecurse_attendance(self, start_datetime, duration, precision=25):
        """
            To split datetime, duration and precision
        """
        res = []
        while (duration > precision):
            res.append((start_datetime, precision))
            start_datetime += timedelta(0, 0, 0, 0, 0, precision)
            duration -= precision
        if duration > precision / 2.0:
            res.append((start_datetime, precision))
        return res

    def _ceil_rounding(self, rounding, datetime):
        """
            round the ceil value.
        """
        minutes = datetime.minute / 60.0 + datetime.second / 60.0 / 60.0
        return math.ceil(minutes * rounding) / rounding

    def _floor_rounding(self, rounding, datetime):
        """
            round the floor value.
        """
        minutes = datetime.minute / 60.0 + datetime.second / 60.0 / 60.0
        return math.floor(minutes * rounding) / rounding

    @api.multi
    @api.depends('employee_id', 'check_in', 'check_out')
    def _get_attendance_duration(self):
        attendance_obj = self.env['resource.calendar.attendance']
        precision = self.env['res.users'].browse(self.env.uid).company_id.working_time_precision
        # 2012.10.16 LF FIX : Get timezone from context
        active_tz = pytz.timezone(self.env.context.get("tz","UTC") if self.env.context and self.env.context.get("tz","UTC") else "UTC")
        str_now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        for attendance in self:
            duration = 0.0
            attendance_start = datetime.strptime(attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT).replace(tzinfo=pytz.utc).astimezone(active_tz)
            next_attendance_date = datetime.strftime(attendance_start, DEFAULT_SERVER_DATETIME_FORMAT)
            if attendance.check_in:
                next_attendance_ids = self.search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '>', attendance.check_in)], order='check_in')
                if next_attendance_ids:
                    next_attendance = next_attendance_ids[0]
                    if next_attendance.check_in and not next_attendance.check_out:
                        # 2012.10.16 LF FIX : Attendance in context timezone
                        raise UserError(_('Incongruent data: sign-in %s is followed by another sign-in') % attendance_start)
                    next_attendance_date = next_attendance.check_in
                if attendance.check_out:
                    # 2012.10.16 LF FIX : Attendance in context timezone
                    attendance_stop = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT).replace(tzinfo=pytz.utc).astimezone(active_tz)
                    duration_delta = attendance_stop - attendance_start
                    # minutes, seconds = divmod(divmod(duration_delta.days * 86400 + duration_delta.seconds, 60)[0], 60)
                    # duration = float('%s.%s'%(str(int(minutes)), str(int(seconds)).zfill(2)))
                    duration = duration_delta.total_seconds() / 60.0 / 60.0
                    duration = round(duration / precision) * precision
            attendance.duration = duration
            attendance.end_datetime = next_attendance_date
            # If contract is not specified: working days = 24/7
            attendance.inside_calendar_duration = duration
            attendance.outside_calendar_duration = 0.0
            active_contract_ids = attendance.employee_id.get_active_contracts(date=str_now[:10])
            if active_contract_ids:
                contract = active_contract_ids[0]
                if contract.resource_calendar_id:
                    # TODO applicare prima arrotondamento o tolleranza?
                    if contract.resource_calendar_id.attendance_rounding:
                        float_attendance_rounding = float(contract.resource_calendar_id.attendance_rounding)
                        rounded_start_hour = self._ceil_rounding(float_attendance_rounding, attendance_start)
                        rounded_stop_hour = self._floor_rounding(float_attendance_rounding, attendance_stop)

                        if abs(1 - rounded_start_hour) < 0.01:  # if shift == 1 hour
                            attendance_start = datetime(attendance_start.year, attendance_start.month,
                                attendance_start.day, attendance_start.hour + 1)
                        else:
                            attendance_start = datetime(attendance_start.year, attendance_start.month,
                                attendance_start.day, attendance_start.hour, int(round(rounded_start_hour * 60.0)))

                        attendance_stop = datetime(attendance_stop.year, attendance_stop.month,
                            attendance_stop.day, attendance_stop.hour, int(round(rounded_stop_hour * 60.0)))

                        # again
                        duration_delta = attendance_stop - attendance_start
                        duration = duration_delta.total_seconds() / 60.0 / 60.0
                        duration = round(duration / precision) * precision
                        attendance.duration = duration

                    attendance.inside_calendar_duration = 0.0
                    attendance.outside_calendar_duration = 0.0
                    calendar_id = contract.resource_calendar_id.id
                    intervals_within = 0

                    # split attendance in intervals = precision
                    # 2012.10.16 LF FIX : no recursion in split attendance
                    splitted_attendances = self._split_norecurse_attendance(attendance_start, duration, precision)
                    counter = 0
                    for atomic_attendance in splitted_attendances:
                        counter += 1
                        centered_attendance = atomic_attendance[0] + timedelta(0, 0, 0, 0, 0, atomic_attendance[1] / 2.0)
                        centered_attendance_hour = centered_attendance.hour + centered_attendance.minute / 60.0 \
                            + centered_attendance.second / 60.0 / 60.0
                        # check if centered_attendance is within a working schedule
                        # 2012.10.16 LF FIX : weekday must be single character not int
                        weekday_char = str(pycompat.unichr(centered_attendance.weekday() + 48))
                        matched_schedule_ids = attendance_obj.search([
                            '&',
                            '|',
                            ('date_from', '=', False),
                            ('date_from', '<=', centered_attendance.date()),
                            '|',
                            ('dayofweek', '=', False),
                            ('dayofweek', '=', weekday_char),
                            ('calendar_id', '=', calendar_id),
                            ('hour_to', '>=', centered_attendance_hour),
                            ('hour_from', '<=', centered_attendance_hour),
                            ])
                        if len(matched_schedule_ids) > 1:
                            raise UserError(_('Wrongly configured working schedule with id %s') % str(calendar_id))
                        if matched_schedule_ids:
                            intervals_within += 1
                            # sign in tolerance
                            if intervals_within == 1:
                                calendar_attendance = matched_schedule_ids[0]
                                attendance_start_hour = attendance_start.hour + attendance_start.minute / 60.0 \
                                    + attendance_start.second / 60.0 / 60.0
                                if attendance_start_hour >= calendar_attendance.hour_from and \
                                    (attendance_start_hour - (calendar_attendance.hour_from +
                                    calendar_attendance.tolerance_to)) < 0.01:  # handling float roundings (<=)
                                    additional_intervals = round(
                                        (attendance_start_hour - calendar_attendance.hour_from) / precision)
                                    intervals_within += additional_intervals
                                    attendance.duration = self.time_sum(
                                        attendance.duration, additional_intervals * precision)
                            # sign out tolerance
                            if len(splitted_attendances) == counter:
                                attendance_stop_hour = attendance_stop.hour + attendance_stop.minute / 60.0 \
                                    + attendance_stop.second / 60.0 / 60.0
                                calendar_attendance = matched_schedule_ids[0]
                                if attendance_stop_hour <= calendar_attendance.hour_to and \
                                    (attendance_stop_hour - (calendar_attendance.hour_to -
                                    calendar_attendance.tolerance_from)) > -0.01:  # handling float roundings (>=)
                                    additional_intervals = round(
                                        (calendar_attendance.hour_to - attendance_stop_hour) / precision)
                                    intervals_within += additional_intervals
                                    attendance.duration = self.time_sum(
                                        attendance.duration, additional_intervals * precision)
                    attendance.inside_calendar_duration = round((intervals_within * precision), 2)
                    # make difference using time in order to avoid rounding errors
                    # inside_calendar_duration can't be > duration
                    attendance.outside_calendar_duration = self.time_difference(
                        attendance.inside_calendar_duration, attendance.duration)
                    if contract.resource_calendar_id.overtime_rounding:
                        if attendance.outside_calendar_duration:
                            overtime = attendance.outside_calendar_duration
                            if contract.resource_calendar_id.overtime_rounding_tolerance:
                                overtime = self.time_sum(overtime,
                                    contract.resource_calendar_id.overtime_rounding_tolerance)
                            float_overtime_rounding = float(contract.resource_calendar_id.overtime_rounding)
                            attendance.outside_calendar_duration = math.floor(
                                overtime * float_overtime_rounding) / float_overtime_rounding

    duration = fields.Float(compute='_get_attendance_duration', store=True, string="Attendance duration")
    end_datetime = fields.Datetime(compute='_get_attendance_duration', store=True, string="End date time")
    outside_calendar_duration = fields.Float(compute='_get_attendance_duration', store=True, string="Overtime")
    inside_calendar_duration = fields.Float(compute='_get_attendance_duration', store=True, string="Duration within working schedule")
