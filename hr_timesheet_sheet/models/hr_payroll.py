# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class hr_payslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = super(hr_payslip, self).get_worked_day_lines(contract_ids, date_from, date_to)
        attendance = [attendance for attendance in res if attendance.get('code') == 'WORK100']
        if attendance:
            attendance = attendance[0]
            attendance['overtime_hours'] = 0.0
            def overtime_hours(employee_id, contract_id, datetime_day):
                overtime = 0.0
                day = datetime_day.strftime("%Y-%m-%d")
                sheet_day_obj = self.env['hr_timesheet_sheet_sheet_day']
                contract = self.env['hr.contract'].browse(contract_id)
                sheet_day_ids = sheet_day_obj.search([('name', '=', day), ('sheet_id.employee_id', '=', employee_id), ('sheet_id.state', '=', 'done')])
                if sheet_day_ids and contract.calculate_overtime:
                   overtime = sheet_day_ids[0].total_overtime
                return overtime
            status_obj = self.env['hr.holidays.status']
            holiday_obj = self.env['hr.holidays']
            attendance_obj = self.env['hr.attendance']
            for contract in contract_ids:
                if not contract.resource_calendar_id:
                    continue
                weekend_overtime = {}
                leaves = {}
                public_overtime = {}
                day_from = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
                day_to = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
                year_id = self.env['year.year'].find(day_from, True)
                nb_of_days = (day_to - day_from).days + 1
                for day in range(0, nb_of_days):
                    working_hours_on_day = 0
                    working_day = (day_from + timedelta(days=day)).strftime("%Y-%m-%d 23:59:59")
                    aa = day_from + timedelta(days=day)
                    working_hours_on_day = contract.employee_id.get_day_work_hours_count(day_from + timedelta(days=day), calendar=contract.resource_calendar_id)
                    overtime_hour = overtime_hours(contract.employee_id.id, contract.id, day_from + timedelta(days=day))
                    if holiday_obj.isPublicDay(working_day, employee_id=contract.employee_id.id, fiscalyear=year_id.id):
                        continue
                    elif holiday_obj.isWorkingDay(working_day, employee_id=contract.employee_id.id):
                        if working_hours_on_day:
                            attendance['overtime_hours'] += overtime_hour
                    elif not working_hours_on_day and contract.calculate_overtime:
                        if overtime_hour > 0:
                            weekend_overtime.update({
                                'name': _("Weekends Working Days paid at 200%"),
                                'sequence': 2,
                                'code': 'WEEKEND_OVERTIME',
                                'number_of_days': (weekend_overtime.get('number_of_days') or 0) + 1,
                                'overtime_hours': (weekend_overtime.get('overtime_hours') or 0) + overtime_hour,
                                'contract_id': contract.id,
                            })
                    elif not holiday_obj.isWorkingDay(working_day, employee_id=contract.employee_id.id,) and contract.calculate_overtime:
                        if overtime_hour > 0:
                            public_overtime.update({
                                'name': _("Public Holiday Working Days paid at 250%"),
                                'sequence': 3,
                                'code': 'HOLIDAY_OVERTIME',
                                'number_of_days': (public_overtime.get('number_of_days') or 0) + 1,
                                'overtime_hours': (public_overtime.get('overtime_hours') or 0) + overtime_hour,
                                'contract_id': contract.id,
                            })
                hours, minutes = attendance_obj.float_time_convert(attendance['overtime_hours']).split(":")
                attendance['overtime_hours'] = float('%02d.%02d' % (int(hours), int(minutes)))
                if weekend_overtime:
                    hours, minutes = attendance_obj.float_time_convert(weekend_overtime['overtime_hours']).split(":")
                    weekend_overtime['overtime_hours'] = float('%02d.%02d' % (int(hours), int(minutes)))
                if public_overtime:
                    hours, minutes = attendance_obj.float_time_convert(public_overtime['overtime_hours']).split(":")
                    public_overtime['overtime_hours'] = float('%02d.%02d' % (int(hours), int(minutes)))
                if weekend_overtime:
                    res += [weekend_overtime]
                if public_overtime:
                    res += [public_overtime]
        return res


class hr_payslip_worked_days(models.Model):
    _inherit = 'hr.payslip.worked_days'

    overtime_hours = fields.Float('Overtime Hours', default=0.0)
