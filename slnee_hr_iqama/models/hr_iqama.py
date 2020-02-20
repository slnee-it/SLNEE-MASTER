# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class HrIqama(models.Model):
    _name = 'hr.iqama'
    _order = 'id desc'
    _inherit = 'mail.thread'
    _description = 'HR IQAMA'

    @api.one
    @api.depends('birthdate')
    def _get_age(self):
        """
            Calculate age, based on inputed birthdate
        """
        if self.birthdate:
            try:
                birthdate = datetime.strptime(self.birthdate, '%Y-%m-%d')
                age_year = (datetime.now() - birthdate).days / 365
                self.age = age_year
            except:
                self.age = 0.0
        else:
            self.age = 0.0

    name = fields.Char('Name(As in Passport)', size=50, help="Name of the dependent", required=True)
    arabic_name = fields.Char('Arabic Name', size=50)
    relation = fields.Selection([('employee', 'Self'), ('child', 'Child'), ('spouse', 'Spouse')], 'Relation')
    employee_id = fields.Many2one('hr.employee', 'Employee',
                                  default=lambda self: self.env['hr.employee'].get_employee())
    job_id = fields.Many2one('hr.job', readonly=True, string='Job Position')
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    branch_id = fields.Many2one('hr.branch', readonly=True, string='Office')
    company_id = fields.Many2one('res.company', readonly=True, string='Company',
                                 default=lambda self: self.env.user.company_id)
    iqama_no = fields.Char('IQAMA Number', size=32, copy=False)
    issue_date = fields.Date('Date of Issue', copy=False)
    expiry_date = fields.Date('Date of Expiry', copy=False)
    profession = fields.Char('Profession', size=64, readonly=False)
    serial_number = fields.Char('Serial Number', copy=False)
    place_of_issue = fields.Char('Place of Issue', copy=False)
    nationality = fields.Many2one('res.country', 'Nationality', readonly=False)
    religion = fields.Selection([('muslim', 'Muslim'), ('non-muslim', 'Non Muslim')], 'Religion', default="muslim")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Waiting Approval'),
                              ('validate', 'Approved'), ('inprogress', 'In Progress'),
                              ('received', 'Issued'), ('need_renewal', 'To be Renewed'),
                              ('refuse', 'Refused')], 'Status', default='draft')
    request_type = fields.Selection([('employee', 'Employee'), ('family', 'Family'), ('new_born', 'New Born Baby')],
                                    'Type', required=True, default='employee')
    approved_date = fields.Datetime('Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    refused_by = fields.Many2one('res.users', 'Refused by', readonly=True, copy=False)
    refused_date = fields.Datetime('Refused on', readonly=True, copy=False)
    age = fields.Float(compute='_get_age', string="Age")
    birthdate = fields.Date("Date of Birth")
    is_saudi = fields.Boolean("Is Saudi")
    description = fields.Text('Description')
    handled_by_id = fields.Many2one('hr.employee', 'Handled By')
    hijri_expiry_date = fields.Char('Date of Expiry(Hijri)')
    iqama_position = fields.Char('IQAMA Position', copy=False)
    arrival_date = fields.Date('Arrival Date(In KSA)')
    current_status = fields.Boolean('In Saudi?')

    @api.onchange('expiry_date', 'issue_date')
    def onchange_expiry_date(self):
        """
            check expiry date is lower than issue date
            return: warning
        """
        if self.expiry_date and self.issue_date and self.expiry_date < self.issue_date:
            raise ValidationError(_('Issue date must be greater then Expiry date.'))

    @api.onchange('request_type')
    def onchange_request_type(self):
        """
            check the request_type, Employee, Family or New Born,
        """
        if self.request_type != 'employee' or not self.employee_id:
            self.birthdate = False
            self.arabic_name = False
            self.name = False
        else:
            self.birthdate = self.employee_id.sudo().birthday or False
            self.arabic_name = self.employee_id.arabic_name or False
            self.name = self.employee_id.name

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
            auto change the values like, Profession, Job, Department, etc depends on selected Employee.
        """
        self.arabic_name = self.employee_id.arabic_name
        self.profession = self.employee_id.sudo().job_id.name
        self.job_id = self.employee_id.sudo().job_id.id
        self.branch_id = self.employee_id.branch_id.id
        self.company_id = self.employee_id.company_id.id
        self.department_id = self.employee_id.department_id.id
        self.nationality = self.employee_id.sudo().country_id.id
        self.religion = self.employee_id.religion
        self.is_saudi = self.employee_id.is_saudi
        if self.request_type == 'employee':
            self.birthdate = self.employee_id.sudo().birthday
            self.name = self.employee_id.name

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        partner=[]
        if values.get('employee_id', False):
            employee_id = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee_id.job_id.id,
                           'department_id': employee_id.department_id.id,
                           'company_id': employee_id.company_id.id,
                           'branch_id': employee_id.branch_id.id,
                           })
        res = super(HrIqama, self).create(values)
        if res.employee_id.parent_id.user_id:
            partner.append(res.employee_id.parent_id.user_id.partner_id.id)
        if res.employee_id.user_id:
            partner.append(res.employee_id.user_id.partner_id.id)
        channel_id=self.env.ref('saudi_hr.manager_channel').id
        res.message_subscribe(partner_ids=partner, channel_ids=[channel_id])
        return res

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: Current record fields data
            :return: Current update record ID
        """
        partner = []
        if values.get('employee_id', False):
            employee_id = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee_id.job_id.id,
                           'department_id': employee_id.department_id.id,
                           'company_id': employee_id.company_id.id,
                           'branch_id': employee_id.branch_id.id or False,
                           })
            if employee_id.user_id:
                partner.append(employee_id.user_id.partner_id.id)
            if employee_id.parent_id.user_id:
                partner.append(employee_id.parent_id.user_id.partner_id.id)
        # channel_id=self.env.ref('saudi_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(HrIqama, self).write(values)

    @api.multi
    def unlink(self):
        """
            Delete/ remove selected record
            :return: Deleted record ID
        """
        for line in self:
            if line.state not in ['draft']:
                raise UserError(_('You cannot remove the IQAMA record which is not in draft state!'))
            return super(HrIqama, line).unlink()

    @api.model
    def check_iqama_expiry(self):
        """
            Send mail for IQAMA Expiry
        """
        template_id = self.env.ref('saudi_hr_iqama.hr_iqama_expiration_email')
        today_date = str(fields.Date.today())
        next_date = datetime.strptime(str(fields.Date.today()), DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=30)
        next_date = datetime.strftime(next_date, DEFAULT_SERVER_DATE_FORMAT)
        for iqama in self.search([('state', '=', 'received'), ('expiry_date', '>=', today_date),
                                  ('expiry_date', '<=', next_date)]):
            diff = datetime.strptime(str(iqama.expiry_date), DEFAULT_SERVER_DATE_FORMAT) - \
                   datetime.strptime(str(fields.Date.today()), DEFAULT_SERVER_DATE_FORMAT)
            if diff.days == 10 and template_id:
                template_id.send_mail(iqama.id, force_send=False, raise_exception=False)
            if diff.days <= 10:
                iqama.iqama_need_renewal()

    @api.multi
    def iqama_confirm(self):
        """
            sent the status of generating his/her iqama in confirm state
        """
        gr_groups_config_obj = self.env['hr.groups.configuration']
        for iqama in self:
            iqama.state = 'confirm'
            gr_groups_config_ids = gr_groups_config_obj.search([('branch_id', '=', iqama.employee_id.branch_id.id or False), ('gr_ids', '!=', False)])
            user_ids = gr_groups_config_ids and [employee.user_id.id for employee in gr_groups_config_ids.gr_ids if employee.user_id] or []
            iqama.sudo().message_subscribe_users(user_ids=user_ids)

    @api.multi
    def iqama_inprogress(self):
        """
            sent the status of generating his/her iqama in inprogress state
        """
        for iqama in self:
            iqama.state = 'inprogress'
            iqama.message_post(message_type="email", subtype='mail.mt_comment',
                               body=_('IQAMA request is In progress'))

    @api.multi
    def iqama_refuse(self):
        """
            sent the status of generating his/her iqama in refuse state
        """
        for iqama in self:
            iqama.write({'state': 'refuse', 'refused_by': self.env.uid, 'refused_date': datetime.today()})
            iqama.message_post(message_type="email", subtype='mail.mt_comment',
                               body=_('IQAMA request is Refused'))

    @api.multi
    def iqama_received(self):
        """
            sent the status of generating his/her iqama in received state by user
        """
        for iqama in self:
            iqama.state = 'received'
            iqama.message_post(message_type="email", subtype='mail.mt_comment',
                               body=_('IQAMA request is Received'))

    @api.multi
    def iqama_validate(self):
        """
            sent the status of generating his/her iqama in validate state
        """
        for iqama in self:
            iqama.write({'state': 'validate', 'approved_by': self.env.uid, 'approved_date': datetime.today()})
            iqama.message_post(message_type="email", subtype='mail.mt_comment',
                               body=_('IQAMA request is Validated'))

    @api.multi
    def iqama_set_to_draft(self):
        """
            sent the status of generating his/her iqama in draft state
        """
        for iqama in self:
            iqama.write({'state': 'draft', 'approved_by': False, 'approved_date': False, 'refused_by': False,
                         'refused_date': False})
            iqama.message_post(message_type="email", subtype='mail.mt_comment',
                               body=_('IQAMA request is reset to draft'))

    @api.multi
    def iqama_need_renewal(self):
        """
            sent the status of generating his/her iqama in renewal state
        """
        for iqama in self:
            iqama.state = 'need_renewal'
            iqama.message_post(message_type="email", subtype='mail.mt_comment',
                               body=_('IQAMA need renewal'))

class EmployeeDependent(models.Model):
    _inherit = 'employee.dependent'

    iqama_no = fields.Char('Iqama Number', size=32)
    issue_date = fields.Date('Date of Issue')
    expiry_date = fields.Date('Date of Expiry')
    serial_number = fields.Char('Serial Number')
    place_of_issue = fields.Char('Place of Issue')


# class one2many_mod_family(fields.One2many):

#     @api.model
#     def get(self):
#         res = {}
#         for id in self.ids:
#             res[id] = []
#         ids2 = self.env[self._obj].search([(self._fields_id, 'in', self.ids), ('type', '!=', 'employee')], limit=self._limit)
#         for r in self.env[self._obj].read(ids2, load='_classic_write'):
#             res[r[self._fields_id]].append(r['id'])
#         return res


# class hr_employee(models.Model):
#     _inherit = 'hr.employee'

#     dependent_ids = one2many_mod_family('hr.iqama', 'employee_id', 'Dependents')
