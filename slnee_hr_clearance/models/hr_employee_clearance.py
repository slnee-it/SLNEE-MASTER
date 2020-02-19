# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo import models, fields, api, _
from datetime import datetime
import time
from werkzeug import urls
from odoo.addons.http_routing.models.ir_http import slug


clearance_states = [('draft','Draft'),
           ('confirm','Waiting Approval'),
           ('done','Done'),
           ('refuse','Refused')]

department_types = [('it','IT'),
           ('admin','Admin'),
           ('finance','Finanace')]
item_state = [('yes','YES'),
           ('no','NO'),
           ('na','N/A')]

clearance_context = False

class ClearanceDepratment(models.Model):
    _name = 'clearance.department'
    _description = "Clearance Department"

    it_dept_id = fields.Many2one('hr.employee.clearance', 'IT Department')
    admin_dept_id = fields.Many2one('hr.employee.clearance', 'Admin Department')
    finance_dept_id = fields.Many2one('hr.employee.clearance', 'Finance Department')
    department_type = fields.Selection(department_types,'Department Type')
    item = fields.Char('Item', required="True")
    item_state = fields.Selection(item_state,'Status', required="True")
    handled_by = fields.Many2one('hr.employee','Handled by')
    remarks = fields.Char('Remarks')

class HrEmployeeClearance(models.Model):

    _name = 'hr.employee.clearance'
    _inherit = 'mail.thread'
    _description = "Employee Clearance"
    _rec_name = 'employee_name'

    @api.model
    def _get_clearance_depts(self,department):
        clearance_dept_lines = []
        clearance_dept_ids = self.env['clearance.department'].search(['&','&',('it_dept_id', '=', False),('admin_dept_id','=',False),('finance_dept_id', '=', False),('department_type', '=', department)])
        for clearance_dept_id in clearance_dept_ids:
            clearance_dept_lines.append((0,0,{'department_type': clearance_dept_id.department_type,
                              'item': clearance_dept_id.item,
                              'item_state': clearance_dept_id.item_state,
                              }))#this dict contain keys which are fields of one2many field
        return clearance_dept_lines

    @api.model
    def _get_login_employee(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
        if employee:
            for emp in employee:
                return emp.id
        else:
            return False

    @api.multi
    def unlink(self):
        for objects in self:
            if objects.state in ['confirm','done']:
                raise UserError(_('You cannot remove the record which is in %s state!')%(objects.state))
        return super(HrEmployeeClearance, self).unlink()

    def context_data(self):
        global clearance_context
        return clearance_context if clearance_context else False

    # @api.multi
    # def action_test_survey(self):
    #     global clearance_context
    #     clearance_context = self._context
    #     ir_model_data = self.env['ir.model.data']
    #     xml_id = ir_model_data.get_object_reference('hr_clearance', 'exit_employee_form')
    #     survey_obj = self.env['survey.survey'].browse(xml_id[1])
    #     name = "Survey"
    #     url  = str(survey_obj.public_url) + "/phantom"
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'name': name,
    #         'target': 'self',
    #         'url': url
    #     }

    # @api.multi
    # def call_print_survey(self):
    #     self.ensure_one()
    #     # if not self.response_id:
    #     #     return self.survey_id.action_print_survey()
    #     # else:
    #     #     response = self.response_id
    #     #     return self.survey_id.with_context(survey_token=response.token).action_print_survey()

    #     # ir_model_data = self.env['ir.model.data']
    #     # xml_id = ir_model_data.get_object_reference('hr_clearance', 'exit_employee_form')
    #     abc = self.survey_id.with_context(survey_token=self.response_id.token)
    #     survey_user_input = self+.env['survey.user_input'].search([('employee_id', '=', self.employee_id.id),('state','=','done'),('survey_id','=',self.survey_id.id)])
    #     if survey_user_input.ids:
    #         survey_obj = self.env['survey.user_input'].browse(survey_user_input.ids[0])
    #         name ="View Answers"
    #         url  = '%s/%s' % (survey_obj.print_url, survey_obj.token)

    #         return {
    #                 'type': 'ir.actions.act_url',
    #                 'name': name,
    #                 'target': 'self',
    #                 'url': url
    #             }
    #     else:
    #         raise UserError(_('Survey not available'))

    def is_survey_true(self):
        ir_model_data = self.env['ir.model.data']
        xml_id = ir_model_data.get_object_reference('slnee_hr_clearance', 'exit_employee_form')
        if self.employee_id and self.employee_id.user_id:
            survey_user_input = self.env['survey.user_input'].search([('state','=','done'),('survey_id','=',self.survey_id.id)])
            if survey_user_input.ids:
                self.is_survey = True

    #Fields Hr Employee Clearance
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, domain="[('date_of_leave', '!=', False), ('active', '=', True)]",default=_get_login_employee)
    line_manager_id = fields.Many2one('hr.employee', 'Manager')
    employee_name = fields.Char(string='Name', related='employee_id.name')
    seniority_date = fields.Date('Seniority Date',default=time.strftime('%Y-%m-%d'))
    last_working_day = fields.Date('Last Day of Work', readonly="True")
    # last_day_in_country = fields.Date('Last Day in the Country')
    location = fields.Many2one('hr.branch', 'Location', readonly="True")
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    # resign_term_date = fields.Date("Resignation/Term Date")
    passport_no = fields.Char('Passport No', readonly="True")
    contact_phone = fields.Char('Contact Phone' ,readonly="True")
    email = fields.Char('Email', readonly="True")
    # letter_to_cilent = fields.Char("Letter to Client")
    it_dept_ids = fields.One2many('clearance.department', 'it_dept_id', 'IT Departments', default=lambda s: s._get_clearance_depts('it'))
    admin_dept_ids = fields.One2many('clearance.department', 'admin_dept_id', 'Admin Departments', default=lambda s: s._get_clearance_depts('admin'))
    finance_dept_ids = fields.One2many('clearance.department', 'finance_dept_id', 'Finance Departments',default=lambda s: s._get_clearance_depts('finance'))
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    approved_date = fields.Datetime('Approved Date', readonly=True)
    approved_by = fields.Many2one('res.users','Approved by', readonly=True)
    state = fields.Selection(clearance_states,'Status',default='draft')#track_visibility='onchange')
    is_survey = fields.Boolean(compute='is_survey_true', string='Is survey')
    it_dept = fields.Boolean('IT Department', track_visibility='onchange')
    hr_dept = fields.Boolean('HR Department', track_visibility='onchange')
    finance_dept = fields.Boolean('Finance Department', track_visibility='onchange')
    survey_id = fields.Many2one('survey.survey', string="Survey", compute='get_default_survey')
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")

    public_url_html = fields.Char("Public link (html version)", compute="_compute_survey_url")

    # def _compute_survey_url(self):
    #     """ Computes a public URL for the survey """
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     for survey in self:
    #         survey.public_url = urls.url_join(base_url, "survey/start/%s/phantom" % (slug(survey.survey_id)))
    #         survey.public_url_html = survey.public_url

    @api.depends('company_id')
    def get_default_survey(self):
        self.ensure_one()
        if self.company_id:
            self.survey_id = self.company_id.survey_id.id

    _sql_constraints = [('emp_uniq', 'unique(employee_id)', 'This employee celarance process is already done.')]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if not self.employee_id:
            self.line_manager_id = False
            self.department_id = False
            self.company_id = False
            self.contact_phone = False
            self.email = False
            self.last_working_day = False
            self.location = False
        else:
            self.line_manager_id = self.employee_id.coach_id.id or False
            self.department_id = self.employee_id.department_id.id or False
            self.company_id = self.employee_id.company_id.id or False
            self.contact_phone = self.employee_id.address_home_id.phone or False
            self.email = self.employee_id.address_home_id.email or False
            self.last_working_day = self.employee_id.date_of_leave or False
            self.location = self.employee_id.branch_id.id or False

    @api.model
    def create(self, Values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if Values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(Values['employee_id'])
            Values.update({'line_manager_id': employee.coach_id.id or False,
                            'department_id': employee.department_id.id or False,
                            'company_id': employee.company_id.id or False,
                            'contact_phone': employee.address_home_id.phone or False,
                            'email': employee.address_home_id.email or False,
                            'last_working_day': employee.date_of_leave or False,
                            'location': employee.branch_id.id or False,
            })
        return super(HrEmployeeClearance,self).create(Values)

    @api.multi
    def write(self, Values):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if Values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(Values['employee_id'])
            Values.update({'line_manager_id': employee.coach_id.id or False,
                            'department_id': employee.department_id.id or False,
                            'company_id': employee.company_id.id or False,
                            'contact_phone': employee.address_home_id.phone or False,
                            'email': employee.address_home_id.email or False,
                            'last_working_day': employee.date_of_leave or False,
                            'location': employee.branch_id.id or False,
            })
        return super(HrEmployeeClearance, self).write(Values)

    # @api.multi
    # def action_send_exit_questionnaire(self):
    #     self.ensure_one()
    #     context = self.env.context
    #     #create a response and link it to this applicant
    #     if not self.response_id:
    #         response = self.env['survey.user_input'].create({'survey_id': self.survey_id.id, 'employee_id': self.employee_id.id})
    #         self.response_id = response.id
    #     else:
    #         response = self.response_id
    #     # grab the token of the response and start surveying
    #     # url = self.survey_id.with_context(survey_token=response.token).action_start_survey()
    #     try:
    #         template_id = self.env.ref('hr_clearance.email_template_send_exit_questionnaire')
    #     except ValueError:
    #         template_id = False

    #     try:
    #         compose_form_id = self.env.ref('mail.email_compose_message_wizard_form')
    #     except ValueError:
    #         compose_form_id = False
    #     if context is None:
    #         context = {}
    #     ctx = context.copy()
    #     ir_model_data = self.env['ir.model.data']
    #     xml_id = ir_model_data.get_object_reference('hr_clearance', 'exit_employee_form')
    #     survey_obj = self.env['survey.survey'].browse(xml_id[1])
    #     url  = str(self.survey_id.public_url) + "/phantom"
    #     self.public_url_html = url
    #     ctx.update({
    #         'default_model': 'hr.employee.clearance',
    #         'default_res_id': self.ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id.id,
    #         'default_composition_mode': 'comment',
    #     })
    #     return {
    #         'name': _('Compose Email'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(compose_form_id.id, 'form')],
    #         'view_id': compose_form_id.id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    @api.multi
    def clearance_approve(self):
        """
            sent the status of generating his/her clearance in Approve state
        """
        self.ensure_one()
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'done','approved_by': user.id, 'approved_date': today})

    @api.multi
    def clearance_cancel(self):
        """
            sent the status of generating his/her clearance in Refuse state
        """
        self.ensure_one()
        self.state = 'refuse'

    @api.multi
    def clearance_confirm(self):
        """
            sent the status of generating his/her clearance in Confirm state
        """
        self.ensure_one()
        if self.it_dept == True and self.hr_dept == True and self.finance_dept == True:
            self.state = 'confirm'
        else:
            raise UserError(_('You cannot confirm request without complete department information.'))

    @api.multi
    def set_to_draft(self):
        """
            sent the status of generating his/her clearance in Set to Draft state
        """
        self.ensure_one()
        self.state = 'draft'


from odoo import models, fields, api, _

class SurveyUserInput(models.Model):
    ''' Metadata for a set of one user's answers to a particular survey '''

    _inherit = "survey.user_input"

    employee_id = fields.Many2one('hr.employee', 'Employee')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')

applicant_context = None

class HrApplicant(models.Model):
    _inherit = "hr.applicant"
    _description = "Applicant"

    def context_data(self):
        global applicant_context
        if applicant_context:
            return applicant_context
        else:
            return False

# class survey_response(osv.osv):
#     _inherit = "survey.response"

#     def create(self, cr, uid, data, context=None):
#         employee_pool = self.pool.get('hr.employee')
#         clearance_pool = self.pool.get('hr.employee.clearance')
#         result = super(survey_response, self).create(cr, uid, data, context=context)
#         employee_ids = employee_pool.search(cr, uid, [('user_id','=',data.get('user_id'))], context=context)
#         if employee_ids:
#             clearance_id = clearance_pool.search(cr, uid, [('employee_id', '=', employee_ids[0])], context=context)
#             res_test = self.pool.get('hr.employee.clearance').write(cr, uid,clearance_id,{'survey_response_id':result}, context=context)
#             return result