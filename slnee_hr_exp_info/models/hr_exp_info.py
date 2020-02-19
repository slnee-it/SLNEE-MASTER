# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime


class HrQualification(models.Model):
    _name = "hr.qualification"

    employee_id = fields.Many2one('hr.employee', 'Employee')
    degree_id = fields.Many2one('hr.recruitment.degree', 'Program')
    university_id = fields.Char('University Name', size=64)
    attended_date_from = fields.Date('Dates Attended(from)')
    attended_date_to = fields.Date('Dates Attended(to)')
    program_type = fields.Selection([('completed', 'Completed'), ('ongoing', 'Ongoing')], 'Program Status', required=True)
    completion_year = fields.Char(string="Year")
    completion_month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                          ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
                          ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                          string='Month')
    field_of_study = fields.Char('Field of Study', size=64)
    grade = fields.Float('Grade(GPA)')
    activities = fields.Text('Activities and Societies')
    description = fields.Text('Description')
    contact_name = fields.Char('Contact Name', size=64)
    contact_phone = fields.Char('Contact Phone No', size=32)
    contact_email = fields.Char('Contact Email', size=64)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)
    percentage = fields.Float(string="Percentage")

    @api.multi
    @api.depends('employee_id')
    def name_get(self):
        """
            to use retrieving the name, combination of `hotel name & room name`
        """
        res = []
        for rec in self:
            name = ''.join([rec.employee_id.name, ' - Qualification'])
            res.append((rec.id, name))
        return res


class HrCertification(models.Model):
    _name = 'hr.certification'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    name = fields.Char('Certification Name', required=True)
    organization_name = fields.Char('Issuing Organization', required=True)
    issue_date = fields.Date('Date of Issue')
    expiry_date = fields.Date('Date of Expiry')
    certification_month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                          ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
                          ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                          string='Month')
    certification_year = fields.Char(string="Year")
    reg_no = fields.Char('Registration No.')
    contact_name = fields.Char('Contact Name', size=64)
    contact_phone = fields.Char('Contact Phone No', size=32)
    contact_email = fields.Char('Contact Email', size=64)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)


class HrExperience(models.Model):
    _name = "hr.experience"
    _inherit = 'mail.thread'
    _description = 'HR Experience'

    is_current_job = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Current Job')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    company = fields.Char('Company', size=128, required=True)
    job_title = fields.Char('Job Title', size=128, required=True)
    location = fields.Char('Location', size=64)
    time_period_from = fields.Date('Time Period(from)', required=True)
    time_period_to = fields.Date('Time Period(to)')
    description = fields.Text('Description')
    contact_name = fields.Char('Contact Name', size=64, required=True)
    contact_phone = fields.Char('Contact Phone No', size=20)
    contact_email = fields.Char('Contact Email', size=64, required=True)
    contact_title = fields.Char('Contact Title', size=24)
    state = fields.Selection([('draft', 'Draft'), ('refuse', 'Refused'), ('approve', 'Approved')], 'Status', readonly=1, default='draft')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)

    @api.multi
    @api.depends('employee_id')
    def name_get(self):
        """
            to use retrieving the name, combination of `hotel name & room name`
        """
        res = []
        for rec in self:
            name = ''.join([rec.employee_id.name or '', ' - Experience'])
            res.append((rec.id, name))
        return res

    @api.multi
    def action_send_mail(self):
        """
            sent an email using email template
        """
        template_id = self.env.ref('slnee_hr_exp_info.email_template_employment_reference', False)
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = self._context.copy()
        ctx.update({
            'default_model': 'hr.experience',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id or False,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def experience_approve(self):
        """
            set the approve state
        """
        for expirence in self:
            expirence.state = 'approve'

    @api.multi
    def experience_refuse(self):
        """
            set the refuse state
        """
        for expirence in self:
            expirence.state = 'refuse'

    # def get_duration(self, exp_id):
    #     """
    #         getting the duration based on the period
    #     """
    #     final_list = []
    #     exp_obj = self.env['hr.experience']
    #     res = {'days_from': '', 'months_from': '', 'years_from': '', 'days_to': '', 'months_to': '', 'years_to': ''}
    #     record = exp_obj.browse(exp_id)
    #     if record.time_period_from:
    #         date_from = datetime.strptime(record.time_period_from, '%Y-%m-%d')
    #         res.update({'days_from': date_from.day, 'months_from': date_from.month, 'years_from': date_from.year})
    #     if record.time_period_to:
    #         date_to = datetime.strptime(record.time_period_to, '%Y-%m-%d')
    #         res.update({'days_to': date_to.day, 'months_to': date_to.month, 'years_to': date_to.year})
    #     final_list.append(res)
    #     return final_list
