# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
from datetime import date, datetime
from dateutil import relativedelta
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
        <td width="100%%">Hello %s,</td>
        <td width="100%%">You are responsible person for the next round.</td>
    </tr>
</table>
</body>
</html>
"""

AVAILABLE_STATES = [
    ('draft', 'New'),
    ('cancel', 'Refused'),
    ('open', 'In Progress'),
    ('pending', 'Pending'),
    ('verification', 'Verification'),
    ('done', 'Hired')
]


class ResDocuments(models.Model):
    _inherit = 'res.documents'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant')


class HRQualification(models.Model):
    _inherit = "hr.qualification"
    _order = 'id desc'

    degree_id = fields.Many2one('hr.recruitment.degree', 'Program')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')


class HRCertification(models.Model):
    _inherit = 'hr.certification'
    _order = 'id desc'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant')


class HRExperience(models.Model):
    _inherit = "hr.experience"
    _order = 'id desc'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant')


class SurveyUserInput(models.Model):
    """
        Metadata for a set of one user's answers to a particular survey
    """
    _inherit = "survey.user_input"
    _order = 'id desc'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')


class HrRecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"
    # _order = 'sequence'

    interview_required = fields.Boolean('Is interview Required?')
    survey_id = fields.Many2one('survey.survey', 'Interview Form')
    # TODO - Jimit - Removed feedback field its not used anymore.
    feedback = fields.Boolean('feedback')
    fold = fields.Boolean('Hide in views if empty', help="This stage is not visible, for example in status bar or kanban view, when there are no records in that stage to display.")
    state = fields.Selection(AVAILABLE_STATES, 'Status', help="The related status for the stage. The status of your document will automatically change according to the selected stage. Example, a stage is related to the status 'Close', when your document reach this stage, it will be automatically closed.")
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of stages. Depends on sequence, movement of stages will be restricted. For ex; One can only move from one stage to its next and previous stages.")
    # TODO - Jimit - Removed Surveyed field its not used anymore.
    surveyed = fields.Boolean('Surveyed')

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for objects in self:
            if objects.state in ['open', 'pending', 'verification', 'done']:
                raise UserError (_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HrRecruitmentStage, self).unlink()

applicant_context = None


class HRApplicant(models.Model):
    _inherit = "hr.applicant"
    _description = "Applicant"
    _order = 'id desc'

    def context_data(self):
        global applicant_context
        if applicant_context:
            return applicant_context
        return False

    @api.multi
    def action_test_survey(self):
        """
            This function opens a window to test the survey
        """
        if not self.stage_id.survey_id:
            raise UserError(_('Please configure Interview Form for % stage!') % (self.stage_id.name))
        global applicant_context
        applicant_context = self._context
        stage = self.stage_id
        name = "Survey"
        url = str(stage.survey_id.public_url) + "/phantom"
        return {
                'type': 'ir.actions.act_url',
                'name': name,
                'target': 'self',
                'url': url,
            }

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for objects in self:
            if objects.state in ['open', 'pending', 'verification', 'done']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (objects.state))
        return super(HRApplicant, self).unlink()

    #TBD - Vera - template not work properly
    # @api.model
    # def create(self, values):
    #     applicant_id = super(HRApplicant, self).create(values)
    #     if applicant_id:
    #         try:
    #             template_id = self.env.ref('slnee_hr_recruitment_custom.email_template_applicant_acknowledge')
    #         except ValueError:
    #             template_id = False
    #         # email_to = values.get('email_from', False)
    #         # email_templates = email_template.browse(template_id)
    #         # email_templates.write({'email_to': email_to, 'reply_to': email_to, 'auto_delete': False})
    #         template_id.send_mail(self.id)
    #     return applicant_id

    @api.multi
    def _get_slnee_country(self):
        """
            Used to get country ids
            return: country_ids which code is SA
        """
        country_ids = self.env['res.country'].search([('code', '=', 'SA')])
        if country_ids:
            return country_ids[0]
        return False

    @api.multi
    def _check_interview_done(self):
        """
            Used to check that interview is done or not
            return: Boolean
        """
        for record in self:
            stage = record.stage_id
            survey_user_input = self.env['survey.user_input'].search([('applicant_id', '=', record.id), ('state', '=', 'done'), ('survey_id', '=', stage.survey_id.id)])
            if record.stage_id and record.stage_id.interview_required:
                record.is_survey = True if survey_user_input.ids else False

    partner_name = fields.Char(size=64, required=True, string='Applicant Name')
    # middle_name = fields.Char(size=128, string='Middle Name')
    # last_name = fields.Char(size=128, string='Last Name', required=True)
    arabic_name = fields.Char('Arabic Name')
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widower', 'Widower')], 'Marital Status')
    job_id = fields.Many2one('hr.job', 'Applied Job')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', default='male')
    date_action = fields.Datetime('Next Action Date')
    email_from = fields.Char('Email', size=128, help="These people will receive email.", required=True)
    feedback_ids = fields.One2many('hr.survey.feedback', 'applicant_id', 'Applicant')
    survey = fields.Many2one(string='Survey', related='stage_id.survey_id')
    passport_number = fields.Integer('Passport Number')
    place_of_issue = fields.Char('Place of Issue', size=128)
    passport_issue_date = fields.Date('Passport Issue Date')
    passport_expiry_date = fields.Date('Passport Expiry Date')
    # profession_on_iqama = fields.Char('Profession on Iqama', size=128)
    date_of_birth = fields.Date('Date of Birth', required=False)
    is_iqama = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Do you have valid national ID / iqama?')
    is_legal_right = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Do you have legal right to work in the country in which you are applying?', default='yes')
    join_immedietly = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Can you join immediately after your notice period?')
    is_legal_guardianship = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Do you hold any legal guardianship?')
    iqama_number = fields.Char('Iqama Number', size=32)
    national_id = fields.Char('National Id', size=32)
    country_id = fields.Many2one('res.country', 'Nationality', required=True, default=_get_slnee_country)
    is_release = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n/a', 'N/A')], 'Is your sponsor ready to give release to your company?')
    no_of_dependents = fields.Integer('Number of Direct Dependents')
    source_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], 'Source Type', default='external')
    internal_reference = fields.Many2one('hr.employee', 'Refered by')
    qualification_ids = fields.One2many('hr.qualification', 'applicant_id', 'Qualifications')
    experience_ids = fields.One2many('hr.experience', 'applicant_id', 'Previous Experience')
    certification_ids = fields.One2many('hr.certification', 'applicant_id', 'Certifications')
    not_joining_reason = fields.Text('Reason')
    is_saudi = fields.Boolean('Saudi/ Non Saudi', default=True)
    # To Do
    # visa_id = fields.Many2one('hr.employee.rec.visa', 'Visa')
    joining_date = fields.Date('Joining Date')
    partner_mobile = fields.Char('Mobile', size=32, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    feedback_done = fields.Boolean('Feedback Done')
    is_survey = fields.Boolean(compute='_check_interview_done', string="Is survey")
    interview_required = fields.Boolean(string="Interview_required", related='stage_id.interview_required')
    state = fields.Selection(AVAILABLE_STATES, related="stage_id.state", string='State')
    # title = fields.Many2one('hr.employee.title', string='Title')
    document_ids = fields.One2many('res.documents', 'applicant_id', 'Document')
    street = fields.Char('Street', size=128)
    street2 = fields.Char('Street2', size=128)
    zip = fields.Char('Zip', change_default=True, size=24)
    city = fields.Char('City', size=128)
    state_id = fields.Many2one("res.country.state", 'State')
    attachment_ids = fields.Many2many('ir.attachment', 'applicant_attachment_rel', 'applicant_id',
                                      'attachment_id', 'Attachments')
    hired_by = fields.Many2one('res.users', 'Hired by', readonly=True, copy=False)
    hired_date = fields.Datetime('Hired on', readonly=True, copy=False)
    refused_by = fields.Many2one('res.users', 'Refused by', readonly=True, copy=False)
    refuse_date = fields.Datetime('Refused on', readonly=True, copy=False)
    user_id = fields.Many2one('res.users', 'Recruiter') # track_visibility='onchange')

    @api.multi
    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        """
            Used to check the birthdate
        """
        if self.date_of_birth and self.gender:
            diff = relativedelta.relativedelta(datetime.today(), datetime.strptime(self.date_of_birth, DEFAULT_SERVER_DATE_FORMAT))
            if self.gender == "male" and abs(diff.years) < 18:
                raise UserError(_("Male employee's age must be greater than 18"))
            elif self.gender == 'female' and abs(diff.years) < 21:
                raise UserError(_("Female Employee's age must be greater than 21."))

    @api.onchange('department_id')
    def onchange_department_id(self):
        """
            Used to set value of job_id and company_id
            return: updated record ID
        """
        res = {'domain': {'job_id': [('id', 'in', [])]}}
        requisition_pool = self.env['hr.job.requisition']
        if self.department_id:
            job_req_ids = requisition_pool.search([('department_id', '=', self.department_id.id), ('state', '=', 'launch')])
            job_ids = [job.job_id.id for job in job_req_ids]
            res['domain'].update({'job_id':[('id', 'in', job_ids)]})
            self.job_id = False
            self.company_id = self.department_id.company_id.id
        return res

    @api.onchange('state_id')
    def onchange_state(self):
        """
            Used to set value of country_id based on state
        """
        if self.state_id:
            self.country_id = self.state_id.country_id.id

    @api.onchange('country_id')
    def onchange_country(self):
        """
            Used to set value of saudi or non saudi based on country
        """
        if self.country_id:
            self.is_saudi = True if self.country_id.code == 'SA' else False

    @api.onchange('joining_date')
    def onchange_joining_date(self):
        """
            used to check joining date
            return: warning
        """
        warning = {}
        if self.joining_date and self.joining_date < str(datetime.today().date()):
            warning.update({
                'title': _('Information'),
                'message': _("Joining Date must be greater than today")})
            self.joining_date = False
        return {'warning':warning}

    @api.multi
    def case_close_with_emp(self):
        """
            Create an hr.employee from the hr.applicants
        """
        state = self.env['hr.recruitment.stage'].search([('state', '=', 'done')])
        job_req_pool = self.env['hr.job.requisition']
        hr_employee = self.env['hr.employee']
        res_partner_obj = self.env['res.partner']
        today = datetime.today()
        emp_id = False
        for applicant in self:
            address_id = contact_name = False
            if applicant.partner_id:
                address_id = res_partner_obj.address_get([applicant.partner_id.id], ['contact'])['contact']
                contact_name = res_partner_obj.name_get([applicant.partner_id.id])[0][1]
            if applicant.job_id and (applicant.partner_name or contact_name):
                job_req_obj = job_req_pool.search([('state', '=', 'launch'), ('job_id', '=', self.job_id.id)])
                if job_req_obj.expected_employees == job_req_obj.no_of_employee:
                    raise UserError(_(" Number of hired employee must be less than expected number of employee in recruitment."))

                applicant.job_id.no_of_hired_employee = applicant.job_id.no_of_hired_employee + 1

                emp_id = hr_employee.create({'name': applicant.partner_name or applicant.name,
                                             'job_id': applicant.job_id.id,
                                             'arabic_name':applicant.arabic_name,
                                             'company_id': applicant.company_id.id,
                                             'address_home_id': address_id,
                                             'gender': applicant.gender,
                                             'department_id': applicant.department_id.id,
                                             'country_id': applicant.country_id.id,
                                             'passport_id': applicant.passport_number or '',
                                             'birthday': applicant.date_of_birth,
                                             'date_of_join': applicant.joining_date,
                                             'marital': applicant.marital_status,
                                             'employee_status': 'active',
                                            })
                job_requisition_ids = job_req_pool.search([('state', '=', 'launch'), ('job_id', '=', applicant.job_id.id)])
                # emp_ids = hr_employee.search([('job_id','=',applicant.job_id.id)])
                if job_req_obj:
                    if job_req_obj.expected_employees == job_req_obj.no_of_employee:
                        job_req_obj.state = 'done'

                if job_requisition_ids and applicant.job_id.no_of_recruitment <= 1:
                    job_req_pool.requisition_done(job_requisition_ids)
                for document_id in applicant.document_ids:
                    document_id.employee_id = emp_id.id
                for qualification_id in applicant.qualification_ids:
                    qualification_id.employee_id = emp_id.id
                for certificate_id in applicant.certification_ids:
                    certificate_id.employee_id = emp_id.id
                for experience_id in applicant.experience_ids:
                    experience_id.employee_id = emp_id.id

                applicant.write({'emp_id': emp_id.id, 'hired_by':self.env.user.id, 'hired_date':today, 'stage_id':state.id})
                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
                emp_id._broadcast_welcome()
            else:
                raise UserError(_('You must define Applied Job for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if emp_id:
            dict_act_window['res_id'] = emp_id.id
        else:
            dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window

    @api.multi
    def view_emp(self):
        """
            This function opens a window to details of employee
            return: employee data
        """
        action_id = self.env.ref('hr.view_employee_form', False)
        dict_data = {
            'view_mode': 'form',
            'views': [(action_id.id, 'form')],
            'view_id': action_id.id,
            'res_id': self.emp_id.id,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'hr.employee',
            'target': 'new'
        }
        return dict_data

    @api.multi
    def send_offer_latter(self):
        """
            This function opens a window to compose an email, to send offer latter
        """
        assert len(self.ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('slnee_hr_recruitment_custom', 'email_template_applicant_offer')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = self._context.copy()
        ctx.update({
            'default_model': 'hr.applicant',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',

        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class HRSurveyFeedback(models.Model):
    _name = 'hr.survey.feedback'
    _order = 'id desc'
    _rec_name = 'stage_id'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant')
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', required=True)
    survey_id = fields.Many2one('survey.survey', 'Survey')
    # survey_response_id = fields.function(_get_survey_responce, type="many2one", relation="survey.response", store=True,string='Response')
    comment = fields.Text('Feedback')
    given_rate = fields.Float('Rate (0-10)')
    feedback_by = fields.Many2one('res.users', 'Feedback by')
    next_round_required = fields.Boolean('Next Round Required', help="Tick this field if further round required in this stage.")
    employee_id = fields.Many2one('hr.employee', 'Responsible Person', help="Responsible person for next round. A notification mail will be send to this person about next round.")

    @api.multi
    def call_print_survey(self):
        """
            this function is used to print survey
            return: survey details or warning
        """
        stage = self.stage_id
        survey_user_input = self.env['survey.user_input'].search([('create_uid', '=', self.env.user.id), ('state', '=', 'done'), ('applicant_id', '=', self.applicant_id.id), ('survey_id', '=', stage.survey_id.id)])
        if survey_user_input.ids:
            survey_obj = survey_user_input.ids[0]
            name = "View Answers"
            url = '%s/%s' % (survey_obj.print_url, survey_obj.token)
            return {
                'type': 'ir.actions.act_url',
                'name': name,
                'target': 'self',
                'url': url
            }
        else:
            raise UserError(_('Survey not available'))

    @api.model
    def default_get(self, fields):
        applicant_pool = self.env['hr.applicant']
        res = super(HRSurveyFeedback, self).default_get(fields)
        applicant_id = self._context.get('active_id', False)
        if applicant_id:
            stage_id = applicant_pool.browse(applicant_id).stage_id.id
            res.update({'stage_id': stage_id})
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        context = self._context
        res = super(HRSurveyFeedback, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        view_type = context.get('is_view', False)
        move_to_next_stage = context.get('move_to_next_stage', False)
        if view_type:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//separator[@string='Response Information']"):
                if view_type == 'feedback':
                    node.set('string', _('Feedback'))
                elif view_type == 'refuse':
                    node.set('string', _('Reason of Refusal'))
            for node in doc.xpath("//button[@string='move_to_next_stage']"):
                if view_type == 'feedback' and not move_to_next_stage == True:
                    node.set('string', _('Move to next stage'))
                if view_type == 'feedback' and move_to_next_stage == True:
                    node.set('string', _('Insert Feedback'))
                if view_type == 'refuse':
                    node.set('string', _('Refuse'))

            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange('given_rate')
    def onchange_rate(self):
        """
            used to check given rate
            return: UserError
        """
        if self.given_rate and self.given_rate < 0 or self.given_rate > 10:
            raise UserError(_('Please enter rate between 0-10.'))

    @api.multi
    def feedback_save(self):
        """
            used to save feedback
            return: True
        """
        self.ensure_one()
        today = (datetime.today()).strftime('%Y-%m-%d %H:%M:%S')
        stage_pool = self.env['hr.recruitment.stage']
        applicant_pool = self.env['hr.applicant']
        applicant_id = self._context.get('active_id', False)
        is_view = self._context.get('is_view', False)
        move_to_next_stage = self._context.get('move_to_next_stage', False)
        for record in self:
            if record.given_rate and record.given_rate < 0 or record.given_rate > 10:
                raise UserError(_('Please enter rate between 0-10.'))
            if record.next_round_required and record.employee_id and is_view != 'refuse':
                body = html_data % (record.employee_id.name)
                mail_obj = self.env['mail.mail']
                vals = {'email_from': 'noreply@localhost',
                        'email_to': record.employee_id.work_email,
                        'state': 'outgoing',
                        'subject': "Reminder for next round",
                        'body_html': body,
                        'auto_delete': True
                        }
                mail_obj.create(vals)
            stage = record.stage_id

            if stage:
                self._cr.execute("""select sequence from hr_recruitment_stage""")
                sequence = [x[0] for x in self._cr.fetchall()]
                sorted_list = sorted(sequence)
                index = sorted_list.index(stage.sequence)
                next_stage = sorted_list[index + 1]
                if stage.interview_required:
                    survey_user_input = self.env['survey.user_input'].search([('create_uid', '=', self.env.user.id), ('state', '=', 'done'), ('survey_id', '=', stage.survey_id.id)])

                    if survey_user_input.ids:
                        self.write({'survey_id': stage.survey_id.id})
                    else:
                        raise UserError(_('Survey is not done.'))
                else:
                    self.write({'survey_id': False})
                self.write({'applicant_id': applicant_id, 'feedback_by': self.env.user.id})
                if move_to_next_stage == True:
                    applicant = applicant_pool.browse(applicant_id)
                    applicant.write({'feedback_done': True})
                if is_view == 'feedback' and not move_to_next_stage == True:
                    stage_id = stage_pool.search([('sequence', '=', next_stage)])
                    for line in stage_id:
                        if line and record.next_round_required == False:
                            applicant = applicant_pool.browse(applicant_id)
                            applicant.stage_id = line.id

        if is_view == 'refuse':
            stage_id = stage_pool.search([('state', '=', 'cancel')])
            if stage_id:
                applicant = applicant_pool.browse(applicant_id)
                applicant.write({'stage_id': stage_id.id, 'refused_by': self.env.user.id, 'refuse_date': today})
            return True
