# -*- coding: utf-8 -*-

import time
from report import report_sxw
from odoo import models, api, fields, _
from datetime import datetime


class Parser(report_sxw.rml_parse):

    def _get_day_of_week(self, day):
        dayofweek = ''
        weekday = datetime.strptime(day, '%Y-%m-%d').weekday()
        if weekday == 0:
            dayofweek = _('Monday')
        elif weekday == 1:
            dayofweek = _('Tuesday')
        elif weekday == 2:
            dayofweek = _('Wednesday')
        elif weekday == 3:
            dayofweek = _('Thursday')
        elif weekday == 4:
            dayofweek = _('Friday')
        elif weekday == 5:
            dayofweek = _('Saturday')
        elif weekday == 6:
            dayofweek = _('Sunday')
        return dayofweek

    def _get_month_name(self, day):
        str_month = ''
        month = datetime.strptime(day, '%Y-%m-%d').month
        if month == 1:
            str_month = _('January')
        elif month == 2:
            str_month = _('February')
        elif month == 3:
            str_month = _('March')
        elif month == 4:
            str_month = _('April')
        elif month == 5:
            str_month = _('May')
        elif month == 6:
            str_month = _('June')
        elif month == 7:
            str_month = _('July')
        elif month == 8:
            str_month = _('August')
        elif month == 9:
            str_month = _('September')
        elif month == 10:
            str_month = _('October')
        elif month == 11:
            str_month = _('November')
        elif month == 12:
            str_month = _('December')
        return str_month

    def _get_days_by_employee(self, employee_id):
        return self.localcontext['data']['form']['days_by_employee'][str(employee_id)]

    def _get_totals_by_employee(self, employee_id):
        return self.localcontext['data']['form']['totals_by_employee'][str(employee_id)]

    def _get_max_per_day(self):
        return self.localcontext['data']['form']['max_number_of_attendances_per_day']

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'days_by_employee': self._get_days_by_employee,
            'totals_by_employee': self._get_totals_by_employee,
            'day_of_week': self._get_day_of_week,
            'max_per_day': self._get_max_per_day,
            'month_name': self._get_month_name,
        })

report_sxw.report_sxw('report.attendance_analysis.calendar_report',
                       'attendance_analysis.calendar_report',
                       'attendance_analysis/report/calendar_report.mako',
                       parser=Parser)
