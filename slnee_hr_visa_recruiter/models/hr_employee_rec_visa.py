# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


html_data = """
<html>
<head>
<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
</head>
<body>
<table border="0" cellspacing="10" cellpadding="0" width="100%%"
    style="font-family: Arial, Sans-serif; font-size: 14">
    <tr>
        <td width="100%%">Hello,%s</td>
    </tr>

    <tr>
        <td>we get your request for %s on %s. Recently we received it. so you can collect it from our branch. </td>
    </tr>

    <tr>
        <td width="100%%">Thank you</td>
        <td width="100%%">%s</td>
    </tr>
</table>
</body>
</html>
"""


class HrEmployeeRecVisa(models.Model):
    _name = 'hr.employee.rec.visa'
    _order = 'id desc'
    _rec_name = 'visa_ref'
    _inherit = ['mail.thread', 'hr.expense.payment']
    _description = "HR Employee Visa requested by recruiter"

    @api.multi
    def _period_of_stay(self):
        """
            Calculate employee visa duration.
        """
        for stay in self:
            if stay.approved_date_from and stay.approved_date_to:
                date_from = datetime.strptime(stay.approved_date_from, DEFAULT_SERVER_DATE_FORMAT)
                date_to = datetime.strptime(stay.approved_date_to, DEFAULT_SERVER_DATE_FORMAT)
                timedelta = date_to - date_from
                diff = timedelta.days
                months = (diff / 30) + 1
                stay.period_of_stay = months

    # Fields Hr Employee Rec Visa
    visa_title = fields.Char(string='Visa Title', size=32)
    reason_of_visa = fields.Selection([('business_visit_visa', 'Business Visit Visa'),
                                       ('commercial_visit_visa', 'Work Visit Visa'),
                                       ('new_join_employee', 'New Work Visa')], string='Type of Visa', required=True)
    visa_type = fields.Selection([('single', 'Single'),
                            ('multi', 'Multiple')], string='Type', default='single')
    visa_for = fields.Selection([('individual', 'Individual'),
                                ('family', 'Family'), ], string='Visa For', required=True, default='individual')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    name = fields.Char(string='name')
    nationality = fields.Many2one('res.country', string='Nationality')
    period_of_stay = fields.Float(string='Visa Duration', compute=_period_of_stay)
    email = fields.Char(string='Email')
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    expense_total = fields.Float(string='Total Expense', digits=dp.get_precision('Account'))
    expense_ids = fields.Many2many('hr.expense', string="Expenses", copy=False)
    requested_date_to = fields.Date(string='Return Date', required=False)
    requested_date_from = fields.Date(string='Departure Date', required=True)
    approved_date_to = fields.Date(string='Approved Date To')
    approved_date_from = fields.Date(string='Approved Date From')
    visa_ref = fields.Char(string='Visa Number')
    required_documents = fields.Text(string='List of Documents Required', readonly=True)
    description = fields.Text(string='Description')
    state = fields.Selection([('draft', 'To Submit'), ('confirm', 'Confirm'), ('inprogress', 'In Progress'),
                              ('received', 'Received'), ('refused', 'Refused')], 'State', default='draft', track_visibility='onchange')  # ,track_visibility='onchange')
    contact_person_ids = fields.One2many('res.partner', 'rec_user_id', string='Contact Person')
    family_visa_ids = fields.One2many('employee.rec.family.visa', 'visa_id', string='Family Details')
    request_by_id = fields.Many2one('hr.employee', string='Request by', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    handled_by_id = fields.Many2one('hr.employee', string='Handled by')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for objects in self:
            if objects.state in ['confirm', 'inprogress', 'received', 'refused']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HrEmployeeRecVisa, self).unlink()

    @api.multi
    @api.depends('employee_id', 'approved_date_from', 'approved_date_to')
    def name_get(self):
        """
            to use retrieving the name, combination of `employee name, date from and date to`
        """
        result = []
        for visa in self:
            name = ''.join([visa.employee_id.name or '', '(', visa.approved_date_from or '',
                            ' to ', visa.approved_date_to or '', ')' or ''])
            result.append((visa.id, name))
        return result

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on selected employee,
            passport, job, department, nationality, email and company id
        """
        self.department_id = False
        self.nationality = False
        self.email = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.nationality = self.employee_id.country_id.id
            self.email = self.employee_id.work_email
            self.company_id = self.employee_id.company_id.id

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        partner = []
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id,
                           'nationality': employee.country_id.id,
                           'email': employee.work_email,
                          })
        res = super(HrEmployeeRecVisa, self).create(values)
        if res.employee_id.parent_id.user_id:
            partner.append(res.employee_id.parent_id.user_id.partner_id.id)
        if res.employee_id.user_id:
            partner.append(res.employee_id.user_id.partner_id.id)
        channel_id=self.env.ref('slnee_hr.manager_channel').id
        res.message_subscribe(partner_ids=partner, channel_ids=[channel_id])
        return res

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: current records fields data
            :return: Current update record ID
        """
        partner = []
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values.get('employee_id'))
            values.update({'department_id': employee.department_id.id,
                           'nationality': employee.country_id.id,
                           'email': employee.work_email,
                           })
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
            if employee.parent_id.user_id:
                partner.append(employee.parent_id.user_id.partner_id.id)
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(HrEmployeeRecVisa, self).write(values)

    @api.one
    @api.constrains('requested_date_from', 'requested_date_to')
    def _check_request_dates(self):
        """
            Check request from date and request to date.
        """
        for contract in self.read(['requested_date_from', 'requested_date_to']):
            if contract['requested_date_from'] and contract['requested_date_to'] and contract['requested_date_from'] > contract['requested_date_to']:
                raise ValidationError(_('Error! Departure Date must be less than Return Date.'))

    @api.one
    @api.constrains('approved_date_from', 'approved_date_to')
    def _check_approved_dates(self):
        """
            Check approve from date and approve to date.
        """
        for contract in self.read(['approved_date_from', 'approved_date_to']):
            if contract['approved_date_from'] and contract['approved_date_to'] and contract['approved_date_from'] > contract['approved_date_to']:
                raise ValidationError(_('Error! Approved Date From must be less than Approved Date To.'))

    @api.onchange('reason_of_visa')
    def onchange_reason_of_visa(self):
        """
            onchange the value based on selected reason for visa,
            required document
        """
        document_list = ""
        if self.reason_of_visa:
            if self.reason_of_visa in ('business_visit_visa', 'commercial_visit_visa'):
                document_list = """
                                1. Date of Ticket
                                2. Clearance Letter of Traffic Payment
                                3. Clearance of Car
                              """
        self.required_documents = document_list


    @api.multi
    def visa_confirm(self):
        """
            sent the status of generating visa his/her in confirm state
        """
        self.ensure_one()
        gr_groups_config_obj = self.env['hr.groups.configuration']
        gr_groups_config_ids = gr_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id), ('gr_ids', '!=', False)])
        user_ids = gr_groups_config_ids and [employee.user_id.id for employee in gr_groups_config_ids.gr_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids=user_ids)
        self.state = 'confirm'

    @api.multi
    def visa_inprogress(self):
        """
            sent the status of generating visa his/her in inprogress state
        """
        self.ensure_one()
        self.state = 'inprogress'

    @api.multi
    def visa_received(self):
        """
            sent the status of generating visa his/her in receive state
        """
        self.ensure_one()
        mail_obj = self.env['mail.mail']
        if self.approved_date_from and self.visa_ref:
            data = {'business_visit_visa': 'Business Visit Visa',
                    'commercial_visit_visa': 'Work Visit Visa',
                    'new_join_employee': 'New Work Visa'}
            body = html_data % (self.employee_id.name, data[self.reason_of_visa], self.create_date, self.env.user.name)
            email_ids = [self.employee_id.work_email, self.create_uid.email]
            for email in email_ids:
                values = {
                        'email_from': self.env.user.email or 'noreply@localhost',
                        'email_to': email,
                        'state': 'outgoing',
                        'subject': "Visa Notification for %s " % data[self.reason_of_visa],
                        'body_html': body,
                        'auto_delete': True
                       }
                mail_id = mail_obj.create(values)
                mail_id.send()
            self.state = 'received'
            self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Received."))
        else:
            raise UserError(_('Please Enter Values For Visa Number, Approved Date From and Approved Date To'))

    @api.multi
    def visa_refuse(self):
        """
            sent the status of generating visa his/her in refuse state
        """
        self.ensure_one()
        self.state = 'refused'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Refused."))

    @api.multi
    def set_draft(self):
        """
            sent the status of generating visa his/her in draft state
        """
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Created."))

    @api.multi
    def generate_expense(self):
        """
            Generate total expense of employee.
            return: created expense ID
        """
        self.ensure_one()
        self.expense_total = self.emp_contribution + self.company_contribution
        product_id = self.env.ref('slnee_hr_visa_recruiter.hr_visa_request')
        name = 'Visa -' + self.name_get()[0][1]
        return self.generate_expense_payment(self, self.description, self.emp_contribution, self.company_contribution, self.payment_mode, name, product_id, self.expense_total)

    @api.multi
    def view_expense(self):
        """
            Redirect to show expense method.
            return: Current record expense ID
        """
        for line in self:
            return self.redirect_to_expense(line.expense_ids)


class EmployeeRecFamilyVisa(models.Model):
    _name = 'employee.rec.family.visa'
    _order = 'id desc'
    _description = 'Employee Family Visa'

    visa_id = fields.Many2one('hr.employee.rec.visa', string='Visa')
    employee_id = fields.Many2one('hr.employee', relation='visa_id.employee_id', string='Employee')
    member_name = fields.Char(string='Member Name (As in Passport)', required=True, size=128)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    birth_date = fields.Date(string='Date of Birth')
    relation = fields.Selection([('child', 'Child'), ('spouse', 'Spouse')], string='Relation')
    id_number = fields.Char(string='ID Number', size=20)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'id desc'

    rec_user_id = fields.Many2one('hr.employee.rec.visa', string='partner')
