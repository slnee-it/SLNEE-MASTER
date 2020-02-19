# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil import relativedelta as rdelta
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
</html>"""

html_data_for_approve = """
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
        <td>we get your request for %s on %s. your request is approved.  </td>
    </tr>

    <tr>
        <td width="100%%">Thank you</td>
        <td width="100%%">%s</td>
    </tr>
</table>
</body>
</html>"""


class HrVisa(models.Model):
    _name = 'hr.visa'
    _order = 'id desc'
    _inherit = ['mail.thread', 'hr.expense.payment']
    _rec_name = 'visa_ref'
    _description = "HR Visa"

    @api.multi
    @api.depends('approved_date_from', 'approved_date_to')
    def _period_of_stay(self):
        """
            Calculate employee visa duration.
        """
        for stay in self:
            if stay.approved_date_from and stay.approved_date_to:
                date_from = datetime.strptime(stay.approved_date_from, DEFAULT_SERVER_DATE_FORMAT)
                date_to = datetime.strptime(stay.approved_date_to, DEFAULT_SERVER_DATE_FORMAT)
                diff = rdelta.relativedelta(date_to, date_from)
                if diff.years > 0:
                    self.years = diff.years
                if diff.months > 0:
                    self.months = diff.months
                if diff.days > 0:
                    self.days = diff.days

    # Fields HR Visa
    visa_title = fields.Char(string='Visa Title', size=32)
    client_id = fields.Char(string='Client Name', size=50)
    reason_of_visa = fields.Selection([('annual_leave', 'Exit re-entry Visa'), ('final_exit', 'Final Exit'),
                                       ('renew_visa', 'Extension of Exit re-entry Visa')], string='Type of Visa', required=True)
    purpose_of_visa = fields.Selection([('training', 'Training'), ('business_trip', 'Business Trip'),
                                        ('annual_vacation', 'Annual Vacation'), ('holiday', 'Holiday'),
                                        ('secondment', 'Secondment'), ('emergency', 'Emergency'),
                                        ('other', 'Other'), ], string='Purpose of Visa', copy=False)
    ticket_type = fields.Selection([('single', 'Single'), ('multi', 'Multiple')], string='Type', default='single', copy=False)
    visa_for = fields.Selection([('individual', 'Individual'), ('family', 'Family'), ],
                                string='Visa For', required=True, default='individual', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].get_employee())
    name = fields.Char(string='name')
    nationality = fields.Many2one('res.country', string='Nationality', readonly=True)
    years = fields.Float(string='Visa Duration', compute=_period_of_stay)
    months = fields.Float(compute=_period_of_stay)
    days = fields.Float(compute=_period_of_stay)
    email = fields.Char(string='Email')
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    expense_total = fields.Float(string='Total Expense', digits=dp.get_precision('Account'))
    expense_ids = fields.Many2many('hr.expense', string="Expenses", copy=False)
    requested_date_to = fields.Date(string='Return Date')
    requested_date_from = fields.Date(string='Departure Date', required=True)
    approved_date_to = fields.Date(string='Approved Date To')
    approved_date_from = fields.Date(string='Approved Date From')
    visa_ref = fields.Char(string='Visa Number')
    old_visa_ref = fields.Char(string='Old Visa Number')
    required_documents = fields.Text(string='List of Documents Required', readonly=True)
    description = fields.Text(string='Description')
    state = fields.Selection([('draft', 'To Submit'), ('confirm', 'Waiting Approval'), ('validate1', 'Approved'),
                              ('inprogress', 'In Progress'), ('received', 'Issued'),
                              ('refused', 'Refused')], string='State', default='draft')
    approved_date = fields.Datetime('Approved Date', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True)
    family_visa_ids = fields.One2many('employee.family.visa', 'visa_id', string='Family Details')
    handled_by = fields.Many2one('hr.employee', string='Handled by')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for objects in self:
            if objects.state in ['confirm', 'validate', 'validate1', 'inprogress', 'received', 'refused']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HrVisa, self).unlink()

    @api.onchange('requested_date_from', 'requested_date_to')
    def _onchange_requested_date(self):
        """
            onchange the value based on requested date from and requested date to,
            raise validation error
        """
        for rec in self:
            if rec.requested_date_to and rec.requested_date_from and rec.requested_date_to < rec.requested_date_from:
                raise ValidationError(_('Departure Date must be greater then Return Date.'))

    @api.onchange('approve_date_to', 'approve_date_from')
    def _onchange_approve_date(self):
        """
            onchange the value based on approve date to and approve date from
            :raise validation error
        """
        for rec in self:
            if rec.approve_date_to and rec.approve_date_from and rec.approve_date_to < rec.approve_date_from:
                raise ValidationError(_('Approve Date to must be greater then Approve Date from.'))

    @api.multi
    @api.depends('employee_id', 'approved_date_from', 'approved_date_to')
    def name_get(self):
        """
            to use retrieving the name, combination of `employee name, date from  & date to`
        """
        result = []
        for visa in self:
            name = ''.join([visa.employee_id.name or '', '(', visa.approved_date_from or '',
                            ' to ', visa.approved_date_to or '', ')' or ''])
            result.append((visa.id, name))
        return result

    @api.model
    def create(self, values):
        """
            Create new record
            :param values: current record fields data
            :return: Newly created record ID
        """
        partner=[]
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'department_id': employee.department_id.id})
        if values.get('reason_of_visa', False):
            if values['reason_of_visa'] == 'final_exit':
                values.update({'required_documents': """
                    1. Date of Ticket
                    2. Clearance Letter from Bank
                    3. Clearance Letter of Traffic Payment(muqeem.com)
                    4. Clearance of Car(muqeem.com)
                                    """})
            if values['reason_of_visa'] == 'annual_leave':
                values.update({'required_documents': """
                    1. Valid Iqama
                    2. Valid Passport
                    3. Clear Traffic Violance (If Any)
                                     """})
        res = super(HrVisa, self).create(values)
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
            Update an existing record
            :param values: current record fields data
            :return: updated record ID
        """
        partner=[]
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values.get('employee_id'))
            values.update({'department_id': employee.department_id.id})
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
            if employee.parent_id.user_id:
                partner.append(employee.parent_id.user_id.partner_id.id)
        if values.get('reason_of_visa', False):
            if values['reason_of_visa'] == 'final_exit':
                values.update({'required_documents': """
                    1. Date of Ticket
                    2. Clearance Letter from Bank
                    3. Clearance Letter of Traffic Payment(muqeem.com)
                    4. Clearance of Car(muqeem.com)
                                    """})
            if values['reason_of_visa'] == 'annual_leave':
                values.update({'required_documents': """
                    1. Valid Iqama
                    2. Valid Passport
                    3. Clear Traffic Violance (If Any)
                                    """})
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(HrVisa, self).write(values)

    @api.one
    @api.constrains('requested_date_from', 'requested_date_to')
    def _check_request_dates(self):
        """
            Check request from and to date.
        """
        for contract in self.read(['requested_date_from', 'requested_date_to']):
            if contract['requested_date_from'] and contract['requested_date_to'] and contract['requested_date_from'] > contract['requested_date_to']:
                raise ValidationError(_('Error! Departure Date must be less than Return Date.'))

    @api.one
    @api.constrains('approved_date_from', 'approved_date_to')
    def _check_approved_dates(self):
        """
            Check approve from and to date.
        """
        for contract in self.read(['approved_date_from', 'approved_date_to']):
            if contract['approved_date_from'] and contract['approved_date_to'] and contract['approved_date_from'] > contract['approved_date_to']:
                raise ValidationError(_('Error! Approved Date From must be less than Approved Date To.'))

    @api.multi
    def visa_confirm(self):
        """
            sent the status of generating visa his/her in reset to confirm state
        """
        self.ensure_one()
        gr_groups_config_obj = self.env['hr.groups.configuration']
        gr_groups_config_ids = gr_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id), ('gr_ids', '!=', False)])
        user_ids = gr_groups_config_ids and [employee.user_id.id for employee in gr_groups_config_ids.gr_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids=user_ids)
        self.state = 'confirm'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Visa Confirmed.'))

    @api.multi
    def visa_validate1(self):
        """
            sent the status of generating visa his/her in reset to validate1 state
        """
        self.ensure_one()
        mail_obj = self.env['mail.mail']
        email_obj = self.env['res.users']
        data = {'annual_leave': 'Exit re-entry Visa',
                'final_exit': 'Final Exit',
                'renew_visa': 'Extension of Exit re-entry Visa'}
        body = html_data_for_approve % (self.employee_id.name, data[self.reason_of_visa], self.create_date,email_obj.name)
        values = {
                'email_from': email_obj.email or 'noreply@localhost',
                'email_to': self.employee_id.work_email,
                'state': 'outgoing',
                'subject': "Visa Notification for %s" % data[self.reason_of_visa],
                'body_html': body,
                'auto_delete': True
               }
        mail_obj.create(values)
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Approved."))
        self.write({'state': 'validate1', 'approved_by': self.env.uid, 'approved_date': datetime.today()})

    @api.multi
    def visa_inprogress(self):
        """
            sent the status of generating visa his/her in reset to inprogress state
        """
        self.ensure_one()
        self.state = 'inprogress'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_('Visa is In progress.'))

    @api.multi
    def visa_received(self):
        """
            sent the status of generating visa his/her in reset to receive state
        """
        self.ensure_one()
        mail_obj = self.env['mail.mail']
        email_obj = self.env['res.users']
        if self.approved_date_from and self.visa_ref:
            data = {'annual_leave': 'Exit re-entry Visa',
                    'final_exit': 'Final Exit',
                    'renew_visa': 'Extension of Exit re-entry Visa'}
            body = html_data % (self.employee_id.name, data[self.reason_of_visa], self.create_date, email_obj.name)
            email_ids = [self.employee_id.work_email, self.create_uid.email]
            for email in email_ids:
                values = {
                        'email_from': email_obj.email or 'noreply@localhost',
                        'email_to': email,
                        'state': 'outgoing',
                        'subject': "Visa Notification for %s " % data[self.reason_of_visa],
                        'body_html': body,
                        'auto_delete': True
                       }
                mail_obj.create(values)
            self.state = 'received'
            self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Received."))
        else:
            raise UserError(_('Please Enter Values For Visa Number, Approved Date From and Approved Date To'))

    @api.multi
    def visa_refuse(self):
        """
            sent the status of generating visa his/her in reset to refuse state
        """
        self.ensure_one()
        self.state = 'refused'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Refused."))

    @api.multi
    def set_draft(self):
        """
            sent the status of generating visa his/her in reset to draft state
        """
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype='mail.mt_comment', body=_("Visa Request Created."))

    @api.onchange('reason_of_visa')
    def onchange_reason_of_visa(self):
        """
            onchange the value based on selected reason of visa,
            required documents
        """
        document_list = ""
        if self.reason_of_visa:
            if self.reason_of_visa == 'final_exit':
                document_list = """
                    1. Date of Ticket
                    2. Clearance Letter from Bank
                    3. Clearance Letter of Traffic Payment(muqeem.com)
                    4. Clearance of Car(muqeem.com)
                                    """
            if self.reason_of_visa == 'annual_leave':
                document_list = """
                    1. Valid Iqama
                    2. Valid Passport
                    3. Clear Traffic Violance (If Any)
                """
        self.required_documents = document_list

    @api.onchange('employee_id', 'reason_of_visa')
    def onchange_employee(self):
        """
            onchange the value based on selected employee of reason of visa,
            job, department, email
        """
        self.department_id = False
        self.nationality = False
        self.email = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.email = self.employee_id.work_email

    @api.multi
    def generate_expense(self):
        """
            Generate employee expense according to operation request
            return: created expense ID
        """
        self.ensure_one()
        self.expense_total = self.emp_contribution + self.company_contribution
        product_id = self.env.ref('slnee_hr_visa.hr_visa_request')
        name = 'Visa -' + self.name_get()[0][1]
        return self.generate_expense_payment(self, self.description, self.emp_contribution, self.company_contribution, self.payment_mode, name, product_id, self.expense_total)

    @api.multi
    def view_expense(self):
        """
            Redirect to employee expense method.
        """
        for line in self:
            return self.redirect_to_expense(line.expense_ids)


class EmployeeFamilyVisa(models.Model):
    _name = 'employee.family.visa'
    _order = 'id desc'
    _description = 'Employee Family Visa'

    visa_id = fields.Many2one('hr.visa', string='Visa')
    employee_id = fields.Many2one('hr.employee', relation='visa_id.employee_id', string="Employee")
    member_name = fields.Char(string='Member Name (As in Passport)', required=True, size=128)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    birth_date = fields.Date(string='Date of Birth')
    relation = fields.Selection([('child', 'Child'), ('spouse', 'Spouse')], string='Relation')
    id_number = fields.Char(string='ID Number', size=20)
