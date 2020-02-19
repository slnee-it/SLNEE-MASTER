# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PublicHolidays(models.Model):
    _name = 'hr.holidays.public'
    _description = 'Public Holidays'
    _order = "name"

    name = fields.Char("Name", required=True)
    state = fields.Selection([('open', 'Open'), ('close', 'Close')], string="Status", required=True, default='open')
    line_ids = fields.One2many('hr.holidays.public.line', 'holidays_id', 'Holiday Dates')
    year = fields.Many2one('year.year', 'Year', required=True)

    @api.multi
    @api.depends('name', 'year')
    def name_get(self):
        """
            Name get combination of `Name` and `Year name`
        """
        res = []
        for holiday in self:
            name = " - ".join([holiday.name, holiday.year.name or ''])
            res.append((holiday.id, name))
        return res

    @api.multi
    def unlink(self):
        """
            remove/ delete existing record if holiday state not in close.
        """
        for holiday in self:
            if holiday.state in ['close']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (object.state))
        return super(PublicHolidays, self).unlink()

    @api.model
    def create(self, values):
        """
            Create a new record
        """
        fiscalyear_obj = self.env['year.year']
        if values.get('year', False):
            year = fiscalyear_obj.browse(values.get('year'))
            if values.get('line_ids', False):
                for line in values.get('line_ids'):
                    if not (line[2]['start_date'] >= year.date_start and line[2]['start_date'] <= year.date_stop) or not (line[2]['end_date'] >= year.date_start and line[2]['end_date'] <= year.date_stop):
                        raise UserError(_('Your Public Holiday must be between this %s to %s Duration.') % (year.date_start, year.date_stop))
        return super(PublicHolidays, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record
        """
        fiscalyear_obj = self.env['year.year']
        hr_holidays_public_line = self.env['hr.holidays.public.line']
        start_dt = end_dt = ''
        if values.get('line_ids', False):
            year = fiscalyear_obj.browse(values.get('year', self.year.id))
            for line in values.get('line_ids'):
                start_dt = line[2] and line[2].get('start_date', False)
                if not start_dt and line[1]:
                    line_obj = hr_holidays_public_line.browse(line[1])
                    start_dt = line_obj.start_date
                end_dt = line[2] and line[2].get('end_date', False)
                if not end_dt and line[1]:
                    line_obj = hr_holidays_public_line.browse(line[1])
                    end_dt = line_obj.end_date
                if not (start_dt >= year.date_start and start_dt <= year.date_stop) or not (end_dt >= year.date_start and end_dt <= year.date_stop):
                    raise UserError(_('Your Public Holiday must be between this %s to %s Duration.') % (year.date_start, year.date_stop))
        return super(PublicHolidays, self).write(values)

    @api.multi
    def set_to_close(self):
        """
            Set the holiday is in close state.
        """
        self.ensure_one()
        self.state = 'close'

    @api.multi
    def set_to_open(self):
        """
            Set the holiday is in open state.
        """
        self.ensure_one()
        self.state = 'open'


class PublicHolidaysLine(models.Model):
    _name = 'hr.holidays.public.line'
    _description = 'Public Holidays Lines'
    _order = "start_date, name desc"

    name = fields.Char('Name', size=128, required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    holidays_id = fields.Many2one('hr.holidays.public', 'Holiday Calendar Year', ondelete="cascade")

    _sql_constraints = [
        ('date_check', "CHECK (start_date <= end_date)", "The start date must be anterior to the end date."),
    ]

    @api.constrains('start_date', 'end_date')
    def check_date_from_to(self):
        """
            Constraints for the holiday is overlaps on same day or not.
        """
        nworking = self.search_count([('start_date', '<=', self.end_date), ('end_date', '>=', self.start_date), ('holidays_id', '=', self.holidays_id.id), ('id', '!=', self.id)])
        if nworking:
            raise ValidationError(_('You can not have holiday that overlaps on same days!'))
