# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class YearYear(models.Model):
    _name = 'year.year'
    _order = 'id desc'
    _description = 'Calendar Year For Public Holiday Duration'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('year.period', 'fiscalyear_id', 'Periods')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code must be unique!'),
    ]

    @api.one
    @api.constrains('date_start', 'date_stop')
    def check_date_from_to(self):
        """
            Check the Start Date must be lower than Stop Date.
        """
        if self.date_start >= self.date_stop:
            raise ValidationError(_('Error!\nThe start date of a calendar year must precede its end date.'))
        nworking = self.search_count([('date_start', '<=', self.date_stop), ('date_stop', '>=', self.date_start), ('id', '!=', self.id)])
        if nworking:
            raise ValidationError(_('You can not have calendar year that overlaps on same year!'))

    @api.multi
    def find(self, dt=None, exception=True, previous=False):
        """
            Find the record depends on Date
        """
        res = self.finds(dt, exception, previous)
        return res and res[0]

    @api.multi
    def finds(self, dt=None, exception=True, previous=False):
        """
            parameters: dt = Date, exception = 'True' or 'False'
            Check the public year configuration is available or not.
        """
        if not dt:
            dt = fields.date.context_today()
        args = [('date_start', '<=', dt), ('date_stop', '>=', dt)]
        company_id = self.env.context['company_id'] if self.env.context.get('company_id') else self.env.user.company_id.id
        args.append(('company_id', '=', company_id))
        ids = self.search(args)
        if not ids and not previous:
            if exception:
                action_id = self.env.ref('hr_fiscal_year.action_public_year')
                msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods and configure a Year.') % dt
                raise RedirectWarning(msg, action_id.id, _('Go to the configuration panel'))
            else:
                return []
        return ids

    @api.multi
    def create_period(self):
        """
            create a new record for Year Period object
        """
        period_obj = self.env['year.period']
        interval = 1
        for fy in self:
            ds = datetime.strptime(fy.date_start, DEFAULT_SERVER_DATE_FORMAT)
            while ds.strftime(DEFAULT_SERVER_DATE_FORMAT) < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)
                if de.strftime(DEFAULT_SERVER_DATE_FORMAT) > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, DEFAULT_SERVER_DATE_FORMAT)
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_stop': de.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True


class AccountPeriod(models.Model):
    _name = "year.period"
    _description = "Year period"
    _order = "date_start"

    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    date_start = fields.Date('Start of Period', required=True)
    date_stop = fields.Date('End of Period', required=True)
    fiscalyear_id = fields.Many2one('year.year', 'Fiscal Year', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the period must be unique!'),
    ]

    @api.constrains('date_stop')
    def _check_year_limit(self):
        """
            check the Year limit
        """
        for obj_period in self:
            if obj_period.date_stop < obj_period.date_start:
                raise ValidationError(_('Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.'))
            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
                    obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
                    obj_period.fiscalyear_id.date_start > obj_period.date_start or \
                    obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                raise ValidationError(_('Error!\nThe duration of the Period(s) is/are invalid'))
            pids = self.search([('date_stop', '>=', obj_period.date_start), ('date_start', '<=', obj_period.date_stop), ('id', '<>', obj_period.id)])
            if pids:
                raise ValidationError(_('Error!\nThe duration of the Period(s) is/are invalid.'))
