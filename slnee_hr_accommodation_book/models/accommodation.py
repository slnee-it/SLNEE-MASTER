# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.exceptions import UserError
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

hotel_states = [('draft', 'Draft'), ('confirm', 'Waiting Approval'), ('validate', 'Approved'), ('booked', 'Booked'),
                ('stay_over', 'Stay Over'), ('refuse', 'Refused'), ('cancel', 'Cancelled')]


class Facility(models.Model):
    _name = "facility"
    _order = 'id desc'
    name = fields.Char('Name', required=True)
    note = fields.Text('Description')


class Villa(models.Model):
    _name = "villa"
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    city = fields.Char(string='City', size=24, required=True)
    per_day_charge = fields.Float(string='Per Day Charge', required=True)
    capacity = fields.Integer(string='Capacity', required=True, default=1)
    contact_no = fields.Char(string='Contact No.', required=True, )
    status = fields.Selection([('vacant', 'Vacant'), ('in_use', 'Occupied'),
                               ('in_service', 'In Service')], string='Status', required=True)


class Room(models.Model):
    _name = "room"
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    hotel_id = fields.Many2one('hotel', string='Hotel', required=True)
    facilities = fields.Many2many('facility', 'room_facilities_rel', 'room_id', 'facility_id', string='Facilities')
    per_day_charge = fields.Float(string='Per Day Charge')

    @api.multi
    @api.depends('hotel_id')
    def name_get(self):
        """
            to use retrieving the name, combination of `hotel name & room name`
        """
        res = []
        for room in self:
            name = ''.join([room.hotel_id.name, ' - ', room.name])
            res.append((room.id, name))
        return res


class Hotel(models.Model):
    _name = "hotel"
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    city = fields.Char(string='City', size=24, required=True)
    contact_no = fields.Char(string='Contact No.', required=True)
    telephone = fields.Char(string='Telephone', size=24)
    email = fields.Char(string='Email', size=24)
    room_ids = fields.One2many('room', 'hotel_id', string='Rooms')
    description = fields.Text(string='Description')


class StayPurpose(models.Model):
    _name = "stay.purpose"
    _order = 'id desc'
    _description = "Purpose Of Stay"

    name = fields.Char(string='Name', required=True)


class Accommodation(models.Model):
    _name = "accommodation"
    _order = 'id desc'
    _inherit = ['mail.thread', 'hr.expense.payment']
    _description = "Accommodation"

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'slnee_hr_accommodation_book.mt_accommodation_new'
        elif 'state' in init_values and self.state == 'confirm':
            return 'slnee_hr_accommodation_book.mt_accommodation_confirm'
        elif 'state' in init_values and self.state == 'validate':
            return 'slnee_hr_accommodation_book.mt_accommodation_validate'
        elif 'state' in init_values and self.state == 'booked':
            return 'slnee_hr_accommodation_book.mt_accommodation_book'
        elif 'state' in init_values and self.state == 'stay_over':
            return 'slnee_hr_accommodation_book.mt_accommodation_stay_over'
        elif 'state' in init_values and self.state == 'refuse':
            return 'slnee_hr_accommodation_book.mt_accommodation_refuse'
        return super(Accommodation, self)._track_subtype(init_values)

    @api.multi
    def _calculate_expense_total(self):
        """
            Calculate total amount for Accommodation.
        """
        for accommodation in self:
            total = sum(line.amount for line in accommodation.accommodation_lines)
            accommodation.expense_total = total

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee(),
                                  help="Employee for which accommodation required")
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True, help="Job for which accommodation required")
    department_id = fields.Many2one('hr.department', string='Department', readonly=True, help="Department for which accommodation required")
    branch_id = fields.Many2one('hr.branch', 'Office', readonly=True)
    city = fields.Char('City', size=24, required=True)
    accommodation_lines = fields.One2many('accommodation.line', 'accommodation_id', string='Accommodation Lines')
    check_in_time = fields.Datetime(string='Check In', required=True)
    check_out_time = fields.Datetime(string='Check Out', required=True)
    state = fields.Selection(hotel_states, string='Status', track_visibility='onchange', default='draft')
    approved_date = fields.Datetime(string='Approved Date', readonly=True, track_visibility='onchange', copy=False)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True, track_visibility='onchange', copy=False)
    expense_total = fields.Float(compute=_calculate_expense_total, string='Total Expense', digits=dp.get_precision('Account'))
    description = fields.Text(string='Description', required=True)
    expense_ids = fields.Many2many('hr.expense', string="Expenses", copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    reason_id = fields.Many2one('stay.purpose', required=True, string='Purpose of Stay', track_visibility='onchange')
    # reason_id = fields.Selection([('internal', 'Internal Meeting'), ('client_related', 'Client Related'),
    #                            ('for_business', 'Business Development'), ('personal', 'Personal'),
    #                            ('new_joiners', 'New Joiners'), ('secondment', 'Secondment')], required=True, string='Purpose of Stay', track_visibility='onchange')

    @api.model
    def create(self, values):
        """
            Create new record
            :param values: current record fields data
            :return: Newly created record ID
        """
        if values.get('employee_id'):
            employee_obj = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee_obj.job_id.id,
                           'department_id': employee_obj.department_id.id,
                           'company_id': employee_obj.company_id.id,
                           'branch_id': employee_obj.branch_id.id,
                           })
        return super(Accommodation, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record
            :param values: current record fields data
            :return: updated record ID
        """
        if values.get('employee_id'):
            employee_obj = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee_obj.job_id.id,
                           'department_id': employee_obj.department_id.id,
                           'company_id': employee_obj.company_id.id,
                           'branch_id': employee_obj.branch_id.id,
                           })
        return super(Accommodation, self).write(values)

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for line in self:
            if line.state in ['validate', 'booked', 'stay_over', 'refuse']:
                raise UserError(_('You cannot remove the accommodation which is in %s state!') % (line.state))
            return super(Accommodation, line).unlink()

    @api.multi
    @api.depends('hotel_id')
    def name_get(self):
        """
            Return name of accommodation with check in & out time.
        """
        res = []
        for accommodation in self:
            name_list = []
            name_list.append(accommodation.employee_id.name or '')
            name_list.extend([' ', accommodation.city or ''])
            name_list.extend([' - (', (datetime.strptime(accommodation.check_in_time, DEFAULT_SERVER_DATETIME_FORMAT)).strftime( '%Y-%m-%d')])
            name_list.extend([' to ', (datetime.strptime(accommodation.check_out_time, DEFAULT_SERVER_DATETIME_FORMAT)).strftime( '%Y-%m-%d'), ')'])
            name = ''.join(name_list)
            res.append((accommodation.id, name))
        return res

    @api.multi
    def confirm_accommodation(self):
        """
            sent the status of generating accommodation record in cancelled state
            :return: True
        """
        self.ensure_one()
        self.state = 'confirm'
        admin_groups_config_obj = self.env['hr.groups.configuration']
        admin_groups_config_ids = admin_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id), ('admin_ids', '!=', False)])
        user_ids = admin_groups_config_ids and [employee.user_id.id for employee in admin_groups_config_ids.admin_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids=user_ids)
        self.message_post(message_type="email", subtype='mail.mt_accommodation_new', body=_('Accommodation Confirmed.'))

    @api.multi
    def accommodation_booked(self):
        """
            sent the status of generating accommodation record in booked state
            :return: True
        """
        self.ensure_one()
        if not self.accommodation_lines:
            raise UserError(_("Please first add accommodation details"))
        self.state = 'booked'

    @api.multi
    def accommodation_refuse(self):
        """
            sent the status of generating accommodation record in refuse state
            :return: True
        """
        self.ensure_one()
        self.state = 'refuse'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Accommodation Refused.'))

    @api.multi
    def set_to_book(self):
        """
            sent the status of generating accommodation record in booked state
            :return: True
        """
        self.ensure_one()
        self.state = 'booked'

    @api.multi
    def set_draft(self):
        """
            sent the status of generating accommodation record in draft state
            :return: True
        """
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Accommodation Created.'))

    @api.multi
    def accommodation_over(self):
        """
            sent the status of generating accommodation record in stay over state
            :return: True
        """
        self.ensure_one()
        if not self.accommodation_lines:
            raise UserError(_('Please add Accommodation Details first !'))
        self.state = 'stay_over'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Accommodation Stay Over.'))

    @api.multi
    def accommodation_validate(self):
        """
            sent the status of generating accommodation record in validate state
            :return: True
        """
        self.ensure_one()
        self.write({'state': 'validate', 'approved_by': self.env.uid, 'approved_date': datetime.today()})
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Accommodation Approved.'))

    @api.onchange('check_out_time')
    def onchange_check_out_time(self):
        """
            onchange the value based on check out time,
            :return: warning
        """
        warning = {}
        if (self.check_in_time and self.check_out_time) and (self.check_out_time <= self.check_in_time):
            warning.update({
                'title': _('Information'),
                'message': _("'Check-Out Time' should be greater than 'Check-In Time'!")})
            self.check_out_time = False
        return {'warning': warning}

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on employee id,
            job, department, company
        """
        self.job_id = False
        self.department_id = False
        self.company_id = False
        self.branch_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            self.branch_id = self.employee_id.branch_id.id

    @api.multi
    def generate_expense(self):
        """
            Generate employee expense.
            return: created expense ID
        """
        self.ensure_one()
        product_id = self.env.ref('slnee_hr_accommodation_book.hotel_accommodation')
        name = 'Accommodation - ' + self.name_get()[0][1]
        return self.generate_expense_payment(self, self.description, self.emp_contribution, self.company_contribution, self.payment_mode, name, product_id, self.expense_total)

    @api.multi
    def view_expense(self):
        """
            Redirect to show expense method.
            :return: current record expense ID
        """
        for line in self:
            return self.redirect_to_expense(line.expense_ids)


class AccommodationLine(models.Model):
    _name = 'accommodation.line'
    _order = 'id desc'
    _inherit = 'mail.thread'
    _description = "Accommodation Lines"

    stay_type = fields.Selection([('villa', 'Villa'), ('hotel', 'Hotel')], string='Stay In', required=True, track_visibility='onchange',
                            default='villa')
    accommodation_id = fields.Many2one('accommodation', string='Accommodation', required=True)
    villa_id = fields.Many2one('villa', string='Villa')
    hotel_id = fields.Many2one('hotel', string='Hotel')
    room_id = fields.Many2one('room', string='Room')
    check_in_time = fields.Datetime(string='Check In', required=True)
    check_out_time = fields.Datetime(string='Check Out', required=True)
    days = fields.Integer(string='Stay Days')
    job_code_id = fields.Char(string='Job Code')
    remarks = fields.Text(string='Remarks')
    amount = fields.Float(string='Amount', track_visibility='onchange', required=True)

    @api.model
    def create(self, values):
        """
            Create accommodation line
            :param values: current record fields data
            :return: Newly created record ID
        """
        if values.get('accommodation_id'):
            self._check_state(values['accommodation_id'])
        return super(AccommodationLine, self).create(values)

    @api.multi
    def write(self, values):
        """
            Update an existing record
            :param values: current record fields data
            :return: updated record ID
        """
        for line in self:
            if values.get('accommodation_id'):
                self._check_state(values['accommodation_id'])
            else:
                self._check_state(line.accommodation_id.id)
        return super(AccommodationLine, self).write(values)

    @api.multi
    def name_get(self):
        """
            return name with check in & out time.
        """
        res = []
        for line in self:
            name_list = []
            name_list.append(line.accommodation_id.employee_id.name or '')
            name_list.extend([', ', line.stay_type or ''])
            name_list.extend([' - (', (datetime.strptime(line.check_in_time, DEFAULT_SERVER_DATETIME_FORMAT)).strftime('%Y-%m-%d')])
            name_list.extend([' to ', (datetime.strptime(line.check_out_time, DEFAULT_SERVER_DATETIME_FORMAT)).strftime('%Y-%m-%d'), ')'])
            name = ''.join(name_list)
            res.append((line.id, name))
        return res

    @api.onchange('stay_type', 'villa_id', 'room_id', 'days')
    def onchange_stay(self):
        """
            onchange the value based on stay_type, villa, room, days
            amount
        """
        if not self.stay_type or not self.days:
            self.amount = 0.0
        stay_record = False
        if self.stay_type == 'villa' and self.villa_id:
            stay_record = self.villa_id
        elif self.stay_type == 'hotel' and self.room_id:
            stay_record = self.room_id
        if stay_record and stay_record.per_day_charge:
            self.amount = stay_record.per_day_charge * self.days

    @api.onchange('check_in_time', 'check_out_time')
    def onchange_time_details(self):
        """
            Set days and checkout time according to check in and check out time.
            return: warning
        """
        warning = {}
        if not self.check_in_time or not self.check_out_time:
            return warning
        if (self.check_in_time and self.check_out_time) and (self.check_in_time <= self.check_out_time):
            diff_days = relativedelta(datetime.strptime(self.check_out_time, DEFAULT_SERVER_DATETIME_FORMAT), datetime.strptime(self.check_in_time, DEFAULT_SERVER_DATETIME_FORMAT))
            self.days = diff_days.days
        else:
            warning.update({
                'title': _('Information'),
                'message': _("'Check-Out Time' should be greater than 'Check-In Time'!")})
            self.check_out_time = False
        return {'warning': warning}

    @api.multi
    def _check_state(self, accommodation_id=False):
        """
            Check accommodation state and raise warning.
            return: True
        """
        accommodation = self.env['accommodation'].browse(accommodation_id)
        if accommodation.state not in ('confirm','booked', 'validate'):
            raise UserError(_("You can't set details for the Accommodation which is not in states mention below ['Booked','Approved'] "))
        return True
