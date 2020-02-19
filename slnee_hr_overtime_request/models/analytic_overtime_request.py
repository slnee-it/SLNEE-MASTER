# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools

html_invitation = """
<html>
<head>
<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
<title>%(name)s</title>
</head>
<body>
<table border="0" cellspacing="10" cellpadding="0" width="100%%"
    style="font-family: Arial, Sans-serif; font-size: 14">
    <tr>
        <td width="100%%">Hello %(emp_name)s,</td>
    </tr>
    <br/><br/>
    <tr>
        <td width="100%%">For <i>%(company)s</i>, You are requested for the overtime works during the following session</td>
    </tr>
</table>
<br/>
<table cellspacing="0" cellpadding="5" border="0" summary=""
    style="width: 90%%; font-family: Arial, Sans-serif; border: 1px Solid #ccc; background-color: #f6f6f6">
    <tr valign="center" align="center">
        <td bgcolor="DFDFDF">
        <h3>%(name)s</h3>
        </td>
    </tr>
    <tr>
        <td>
        <table cellpadding="8" cellspacing="0" border="0"
            style="font-size: 14" summary="Eventdetails" bgcolor="f6f6f6"
            width="90%%">
            <tr>
                <td width="21%%">
                <div><b>Start Date</b></div>
                </td>
                <td><b>:</b></td>
                <td>%(start_date)s</td>
                <td width="15%%">
                <div><b>End Date</b></div>
                </td>
                <td><b>:</b></td>
                <td width="25%%">%(end_date)s</td>
            </tr>
            <tr>
                <td width="21%%">
                <div><b>Daily Overtime Duration</b></div>
                </td>
                <td><b>:</b></td>
                <td>%(duration)s</td>
            </tr>
            <tr valign="top">
                <td><b>Description</b></td>
                <td><b>:</b></td>
                <td colspan="3">%(description)s</td>
            </tr>
        </table>
        </td>
    </tr>
</table>
<br/>
<table border="0" cellspacing="10" cellpadding="0" width="100%%"
    style="font-family: Arial, Sans-serif; font-size: 14">
    <tr>
        <td width="100%%">From:</td>
    </tr>
    <tr>
        <td width="100%%">%(user)s</td>
    </tr>
    <tr valign="top">
        <td width="100%%">-<font color="a7a7a7">-------------------------</font></td>
    </tr>
    <tr>
        <td width="100%%"> <font color="a7a7a7">%(sign)s</font></td>
    </tr>
</table>
<table border="0" cellspacing="10" cellpadding="0" width="100%%"
    style="font-family: Arial, Sans-serif; font-size: 14">
    <tr>
        <td width="100%%">You can submit your Response, through your login</td>
    </tr>
</table>
</body>
</html>
"""

class AnalyticOvertime(models.Model):
    _name = 'analytic.overtime'
    _order = 'id desc'
    _description = "Analytic Overtime"
    _inherit = ['mail.thread']

    name = fields.Char('Task Name', required=True,track_visibility='onchange')
    date = fields.Date('Start Date', required=True,track_visibility='onchange')
    end_date = fields.Date('End Date', required=True,track_visibility='onchange')
    duration = fields.Float('Daily Duration', digits=(2, 2),track_visibility='onchange')
    description = fields.Text('Description')
    state = fields.Selection([
        ('tentative', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('waiting', 'Waiting Answer'),
        ('done', 'Done'),
        ], 'Status', readonly=True, default='tentative',track_visibility='onchange')
    user_id = fields.Many2one('res.users', 'Responsible',track_visibility='onchange', default=lambda self: self.env.uid)
    attendee_ids = fields.One2many('analytic.overtime.attendee', 'analytic_overtime_id', string='Attendees')
    target = fields.Selection([('country', 'Country Wise'), ('state', 'State Wise'), ('company', 'Company Wise'),
                                ('department', 'Department Wise'), ('job', 'Job Profile Wise')], string="Target Group")
    country_ids = fields.Many2many('res.country', 'country_analytic_overtime_rel', 'analytic_overtime_id', 'country_id', string="Countries",track_visibility='onchange')
    state_ids = fields.Many2many('res.country.state', 'state_analytic_overtime_rel', 'analytic_overtime_id', 'state_id', string="States")
    company_ids = fields.Many2many('res.company', 'company_analytic_overtime_rel', 'analytic_overtime_id', 'company_id', string="Companies")
    department_ids = fields.Many2many('hr.department', 'department_analytic_overtime_rel', 'analytic_overtime_id', 'department_id', string="Departments")
    job_ids = fields.Many2many('hr.job', 'job_analytic_overtime_rel', 'analytic_overtime_id', 'job_id', string="JOB Profiles")

    _sql_constraints = [
        ('check_dates', 'CHECK(date <= end_date)', 'Start Date must be greater than End Date!'),
    ]

    @api.onchange('user_id', 'target', 'country_ids', 'state_ids', 'company_ids', 'department_ids', 'job_ids')
    def onchange_target(self):
        company_obj = self.env['res.company']
        emp_obj = self.env['hr.employee']
        attendees = []

        def get_mail(employee_id):
            email = ''
            if employee_id:
                employee = emp_obj.browse(employee_id)
                email = (employee.work_email) or (employee.user_id.email) or ''
                return {'value': {'email': email}}
            return {'value': {'email': email}}

        if self.target == 'country':
            if not self.country_ids:
                self.department_ids = False
                self.job_ids = False
                self.company_ids = False
                self.state_ids = False
                self.attendee_ids = []
            else:
                company_ids = company_obj.search([('partner_id.country_id', 'in', self.country_ids.ids)])
                for emp_id in emp_obj.search([('company_id', 'in', company_ids.ids)]):
                    res = get_mail(emp_id.id)
                    attendees.append({'user_id': self.user_id or self.env.uid, 'employee_id': emp_id, 'email': res['value']['email'] or '', 'state': 'needs-action', })
                self.attendee_ids = attendees

        elif self.target == 'state':
            if not self.state_ids:
                self.department_ids = False
                self.job_ids = False
                self.country_ids = False
                self.company_ids = False
                self.attendee_ids = []
            else:
                company_ids = company_obj.search([('partner_id.state_id', 'in', self.state_ids.ids)])
                for emp_id in emp_obj.search([('company_id', 'in', company_ids.ids)]):
                    res = get_mail(emp_id.id)
                    attendees.append({'user_id': self.user_id or self.env.uid, 'employee_id': emp_id, 'email': res['value']['email'] or '', 'state': 'needs-action', })
                self.attendee_ids = attendees

        elif self.target == 'company':
            for emp_id in emp_obj.search([('company_id', 'in', self.company_ids.ids or [])]).ids:
                res = get_mail(emp_id)
                attendees.append({'user_id': self.user_id or self.env.uid, 'employee_id': emp_id, 'email': res['value']['email'] or '', 'state': 'needs-action', })
            self.department_ids = False
            self.job_ids = False
            self.country_ids = False
            self.state_ids = False
            self.attendee_ids = attendees

        elif self.target == 'department':
            for emp_id in emp_obj.search([('department_id', 'in', self.department_ids.ids or [])]).ids:
                res = get_mail(emp_id)
                attendees.append({'user_id': self.user_id or self.env.uid, 'employee_id': emp_id, 'email': res['value']['email'] or '', 'state': 'needs-action', })
            self.job_ids = False
            self.country_ids = False
            self.company_ids = False
            self.state_ids = False
            self.attendee_ids = attendees

        elif self.target == 'job':
            for emp_id in emp_obj.search([('job_id', 'in', self.job_ids.ids or [])]).ids:
                res = get_mail(emp_id)
                attendees.append({'user_id': self.user_id or self.env.uid, 'employee_id': emp_id, 'email': res['value']['email'] or '', 'state': 'needs-action', })
            self.department_ids = False
            self.country_ids = False
            self.company_ids = False
            self.state_ids = False
            self.attendee_ids = attendees
        else:
            self.department_ids = False
            self.job_ids = False
            self.country_ids = False
            self.company_ids = False
            self.state_ids = False
            self.attendee_ids = False

    @api.multi
    def create_attendees(self):
        res = False
        current_user = self.env.user
        for analytic in self:
            if not analytic.attendee_ids:
                raise UserError(_('Please create some inventation details!'))
            for att in analytic.attendee_ids:
                if not att.email:
                    continue
                if not att.mail_sent:
                    mail_to = att.email
                    if mail_to and (current_user.email or analytic.user_id.email or tools.config.get('email_from', False)):
                        res = att._send_mail(mail_to, email_from=current_user.email or analytic.user_id.email or tools.config.get('email_from', False))
                        if res:
                            att.mail_sent = True
        self.state = 'waiting'

    @api.multi
    def do_confirm(self):
        """
            sent the status of overtime request in Confirm state
        """
        self.ensure_one()
        self.state = 'confirmed'

    @api.multi
    def do_tentative(self):
        """
            sent the status of overtime request in Tentative state
        """
        self.ensure_one()
        self.state = 'tentative'

    @api.multi
    def do_done(self):
        """
            sent the status of overtime request in Done state
        """
        self.ensure_one()
        self.state = 'done'

    @api.multi
    def do_cancel(self):
        """
            sent the status of overtime request in Cancel state
        """
        self.ensure_one()
        self.state = 'cancelled'

    @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'tentative' state
        """
        for rec in self:
            if not rec.state in ['tentative']:
                raise UserError(_('In order to delete a confirmed analytic overtime request, you must set to draft it before!'))
        return super(AnalyticOvertime, self).unlink()

    @api.multi
    def copy(self, default=None):
        return super(AnalyticOvertime, self.with_context(from_copy=True)).copy(default)


class AnalyticOvertimeAttendee(models.Model):
    _name = "analytic.overtime.attendee"
    _order = 'id desc'
    _description = "Analytic Overtime Attendee"
    _rec_name = 'analytic_overtime_id'
    _inherit = ['mail.thread']

    analytic_overtime_id = fields.Many2one('analytic.overtime', 'Analytic Overtime Request', ondelete='cascade', domain=[('state', 'not in', ['cancelled','done'])], track_visibility='onchange')
    state = fields.Selection([('needs-action', 'Waiting Answer'),
                  ('declined', 'Declined'), ('accepted', 'Accepted')],
                  'Status', readonly=True,
                  help="Status of the attendee's participation", default='needs-action', track_visibility='onchange')
    user_id = fields.Many2one('res.users', 'User', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, track_visibility='onchange')
    mail_sent = fields.Boolean('Mail Sent', default=False)
    email = fields.Char('Email', size=124, help="Email of Invited Person")

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
            This function is used set value of email
        """
        self.email = (self.employee_id.work_email) or (self.employee_id.user_id.email) or ''

    @api.multi
    def _send_mail(self, mail_to, email_from=tools.config.get('email_from', False)):
        """
            Send mail for event invitation to event attendees.
            @param email_from: email address for user sending the mail
            @return: True
        """
        body = " "

        company = self.env.user.company_id.name
        group_ids = [self.env.ref('base.group_user').id, self.env.ref('hr_attendance.group_hr_attendance').id]
        user_ref = self.env['res.users']

        for att in self:
            if not att.employee_id.user_id:
                raise UserError(_("Please assign user to %s.") % (att.employee_id.name))
            sign = att.user_id and att.user_id.signature or ''
            sign = '<br>'.join(sign and sign.split('\n') or [])
            if att.employee_id:
                att_infos = []
                sub = att.analytic_overtime_id.name or ''
                # dates and times are gonna be expressed in `tz` time (local timezone of the `uid`)
                body_vals = {'name': att.analytic_overtime_id.name or '',
                            'start_date': att.analytic_overtime_id.date,
                            'end_date': att.analytic_overtime_id.end_date,
                            'description': att.analytic_overtime_id.description or '-',
                            'attendees': '<br>'.join(att_infos),
                            'user': att.user_id.name or 'Odoo User',
                            'sign': sign,
                            'company': company,
                            'emp_name': att.employee_id.name,
                            'duration': att.analytic_overtime_id.duration or 0}

                body = html_invitation % body_vals
                if mail_to and email_from:
                    vals = {'email_from': email_from,
                            'email_to': mail_to,
                            'recipient_ids': [(6, 0, [att.employee_id.user_id.partner_id.id])],
                            'partner_ids': [(6, 0, [att.employee_id.user_id.partner_id.id])],
                            'needaction_partner_ids':[(6, 0, [att.employee_id.user_id.partner_id.id])],
                            'state': 'outgoing',
                            'subject': sub,
                            'body_html': body,
                            'body': body,
                            'auto_delete': True}
                    mail_id = self.env['mail.mail'].create(vals)
                    mail_id.send()
        return True

    @api.multi
    def do_tentative(self):
        """
            update the status to tentative
        """
        self.ensure_one()
        self.state = 'tentative'

    @api.multi
    def do_accept(self):
        """
            update the status to accepted
        """
        self.ensure_one()
        self.state = 'accepted'

    @api.multi
    def do_decline(self):
        """
            update the status to declined
        """
        self.ensure_one()
        self.state = 'declined'

    @api.model
    def create(self, vals):
        """
            Create a new record
            return: Newly created record ID
        """
        if self._context.get('from_copy', False):
            vals.update(mail_sent=False)
        return super(AnalyticOvertimeAttendee, self).create(vals)
