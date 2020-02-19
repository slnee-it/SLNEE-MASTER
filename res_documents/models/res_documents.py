# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _
from ast import literal_eval


class ResDocumentType(models.Model):
    _name = 'res.document.type'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('code', 'unique(code)', 'Code must be unique per Document!'),
    ]


class ResDocuments(models.Model):
    _name = 'res.documents'
    _inherit = ['mail.thread']

#     applicant_id =  fields.Many2one('hr.applicant', 'Applicant')
    type_id = fields.Many2one('res.document.type', 'Type')
    doc_number = fields.Char('Number', size=128)
    issue_place = fields.Char('Place of Issue', size=128)
    issue_date = fields.Date('Date of Issue', track_visibility='onchange')
    expiry_date = fields.Date('Date of Expiry', track_visibility='onchange')
    notes = fields.Text('Notes')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    manager_id = fields.Many2one('hr.employee', string='Manager', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company')
    is_visible_on_report = fields.Boolean('Visible on Report')
    profession = fields.Char('Profession', size=32)
    hijri_expiry_date = fields.Char('Date of Expiry(Hijri)')
    position = fields.Char('Position')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('issue', 'Issued'),
            ('refuse', 'Refused'),
            ('renew', 'Renew'),
            ('expiry', 'Expiry')], string='Status', readonly=True, copy=False, default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        res = super(ResDocuments, self).create(vals)
        partner = []
        partner.append(self.env.user.partner_id.id)
        if res.manager_id.user_id:
            partner.append(res.manager_id.user_id.partner_id.id)
        if res.employee_id.user_id:
            partner.append(res.employee_id.user_id.partner_id.id)
        channel_id = self.env.ref('slnee_hr.manager_channel').id
        res.message_subscribe(partner_ids=partner, channel_ids=[channel_id])
        return res

    @api.multi
    def write(self, vals):
        partner=[]
        if vals.get('manager_id'):
            employee = self.env['hr.employee'].browse(vals.get('manager_id'))
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(ResDocuments, self).write(vals)

    @api.multi
    @api.depends('employee_id', 'type_id', 'doc_number')
    def name_get(self):
        """
            Return name of document with employee name, document type & document number.
        """
        result = []
        for doc in self:
            name = doc.employee_id.name + ' ' + doc.type_id.name + ' ' + doc.doc_number
            result.append((doc.id, name))
        return result

    @api.model
    def run_scheduler(self):
        """
            cron job for automatically sent an email,
            sent notification, your document expired after 1 month.
        """
        try:
            template_id = self.env.ref('res_documents.email_template_res_documents_notify')
        except ValueError:
            template_id = False
        for document in self.search([]):
            if document.expiry_date and document.employee_id.user_id and template_id:
                if str(datetime.now().date()) == str((datetime.strptime(document.expiry_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=+1)).date()):
                    email_to = ''
                    user = document.employee_id.user_id
                    if user.email:
                        email_to = email_to and email_to + ',' + user.email or email_to + user.email
                    template_id.write({'email_to': email_to, 'reply_to': email_to, 'auto_delete': False})
                    template_id.send_mail(document.id, force_send=True)
            if document.expiry_date and document.expiry_date == str(datetime.now().date()) and document.state == 'issue':
                document.state = 'expiry'
                if document.state == 'expiry':
                    ir_model_data = self.env['ir.model.data']
                    try:
                        template_id = ir_model_data.get_object_reference('res_documents', 'email_template_res_document_expire')[1]
                    except ValueError:
                        template_id = False
                    if template_id:
                        template = self.env['mail.template'].browse(template_id)
                        template.send_mail(document.id, force_send=True,raise_exception=False,email_values=None)
        return True

    @api.multi
    def action_send_mail(self):
        """
            send mail using mail template
        """
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('res_documents', 'email_template_res_document')[1]
        except ValueError:
            template_id = False
        if template_id:
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True,raise_exception=False,email_values=None)
        return True

    @api.multi
    def set_draft(self):
        """
            sent the status of generating Document record in draft state
        """
        self.state = 'draft'

    @api.multi
    def document_submit(self):
        """
            sent the status of generating Document record in confirm state
        """
        self.state = 'confirm'

    @api.multi
    def document_issue(self):
        """
            sent the status of generating Document record in issue state and get issue date
        """
        self.action_send_mail()
        return self.write({'state':'issue', 'issue_date': datetime.today()})

    @api.multi
    def document_refuse(self):
        """
            sent the status of generating Document record in refuse state
        """
        self.state = 'refuse'

    @api.multi
    def document_renew(self):
        """
            sent the status of generating Document record is renew
        """
        self.state = 'renew'
        self.expiry_date = ''
        self.issue_date = ''


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    document_ids = fields.One2many('res.documents', 'employee_id', 'Document')
    documents_count = fields.Integer(string='Documents', compute="_compute_documents")

    @api.multi
    def _compute_documents(self):
        """
            count total document related employee
        """
        for employee in self:
            documents = self.env['res.documents'].search([('employee_id', '=', employee.id)])
            employee.documents_count = len(documents) if documents else 0

    @api.multi
    def action_documents(self):
        """
            Show employee Documents
        """
        document_ids = self.env['res.documents'].search([('employee_id', '=', self.id)])
        action = self.env.ref('res_documents.action_res_documents')
        result = action.read()[0]
        if len(document_ids) > 1:
            result['domain'] = [('id', 'in', document_ids.ids)]
        elif len(document_ids) == 1:
            res = self.env.ref('res_documents.res_documents_view_form', False)
            result['views'] = [(res.id, 'form')]
            result['res_id'] = document_ids[0].id
        else:
            result['domain'] = [('id', 'in', document_ids.ids)]
        context = literal_eval(result['context'])
        context.update({'default_employee_id': self.id,
                        'default_manager_id': self.coach_id.id,
                        'from_employee': True,
                        'search_default_group_state': 0,
                        'search_default_group_employee_id': 0})
        result['context'] = context
        return result
