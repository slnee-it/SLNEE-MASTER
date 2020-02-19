# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class HrAdminCopyCenter(models.Model):
    _name = 'copy.center'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'hr.expense.payment']
    _order = 'id desc'

    @api.multi
    def _amount_all(self):
        """
            Calculate total amount for copy center.
        """
        for rec in self:
            total = 0.0
            for line in rec.product_ids:
                total += line.price_subtotal
            rec.amount_total = total

    request_type = fields.Selection([('confidential', 'CONFIDENTIAL'),
                                     ('non_confidential', 'NON-CONFIDENTIAL')], string='Request Type',
                                    default='non_confidential')
    employee_id = fields.Many2one('hr.employee', required=True, string='Employee', default=lambda self: self.env['hr.employee'].get_employee())
    job_id = fields.Many2one('hr.job', readonly=True, string='Job Position')
    email_contact = fields.Char(string='Email Contact', readonly=True)
    mobile_contact = fields.Char(string='Mobile Contact', readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    expense_total = fields.Float(string='Total Expense', digits=dp.get_precision('Account'))
    job_description = fields.Char(string='Job Description', size=200)
    date_submited = fields.Date(string='Submit Date', required=True, default=datetime.strftime(datetime.now(), '%Y-%m-%d'))
    date_required = fields.Date(string='Require Date', required=True, default=datetime.strftime(datetime.now(), '%Y-%m-%d'))
    paper = fields.Selection([('a4', 'A4'), ('a3', 'A3'), ('cardstock', 'Cardstock'),
                              ('letterhead', 'Letterhead'),
                              ('letterhead_2nd_sheets', 'Letterhead 2nd Sheets'),
                              ('colour_paper', 'Colour Paper'),
                              ('other', 'Other')], string='Paper', default='a4')
    copy_style = fields.Selection([('1 sided to 1 sided', '1 sided to 1 sided'),
                                   ('1 sided to 2 sided', '1 sided to 2 sided'),
                                   ('2 sided to 1 sided', '2 sided to 1 sided'),
                                   ('2 sided to 2 sided', '2 sided to 2 sided')], string='Copy Style',
                                  default='1 sided to 1 sided')
    orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], string='Orientation', default='portrait')
    delivery_instructions = fields.Selection([('deliver_to_employee_desk', 'Deliver to employee desk'),
                                              ('deliver_to_another_employee', 'Deliver to another employee'),
                                              ('employee_to_retrieved_from_copy_centre', 'Employee to retrieved from copy centre '),
                                              ('other_delivery_request ', 'Other delivery request')], string='Delivery Instructions',
                                             default='employee_to_retrieved_from_copy_centre')
    product_ids = fields.One2many('product.line', 'copy_center_id', string='Product')
    special_instructions = fields.Text(string='Special Instructions')
    amount_total = fields.Float(compute=_amount_all, string='Total Amount')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Waiting Approval'), ('validate', 'Approved'),
                              ('in_progress', 'In Progress'), ('done', 'Done'),
                              ('refuse', 'Refused')], 'State', track_visibility='onchange', default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    approved_date = fields.Datetime(string='Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True, copy=False)
    expense_ids = fields.Many2many('hr.expense', string="Expenses", copy=False)

    @api.model
    def create(self, value):
        """
            Create a new record
            :param value: Current record fields data
            :return: Newly created record ID
        """
        partner=[]
        if value.get('employee_id'):
            employee_obj = self.env['hr.employee'].browse(value['employee_id'])
            value.update({'job_id': employee_obj.job_id.id,
                          'department_id': employee_obj.department_id.id,
                          'email_contact': employee_obj.work_email,
                          'mobile_contact': employee_obj.mobile_phone})
        res = super(HrAdminCopyCenter, self).create(value)
        if res.employee_id.parent_id.user_id:
            partner.append(res.employee_id.parent_id.user_id.partner_id.id)
        if res.employee_id.user_id:
            partner.append(res.employee_id.user_id.partner_id.id)
        channel_id=self.env.ref('slnee_hr.manager_channel').id
        res.message_subscribe(partner_ids=partner, channel_ids=[channel_id])
        return res

    @api.multi
    def write(self, value):
        """
            Update an existing record.
            :param value: Current record fields data
            :return: Current update record ID
        """
        partner=[]
        if value.get('employee_id'):
            employee = self.env['hr.employee'].browse(value['employee_id'])
            value.update({'job_id': employee.job_id.id,
                          'department_id': employee.department_id.id,
                          'email_contact': employee.work_email,
                          'mobile_contact': employee.mobile_phone})
            if employee.user_id:
                partner.append(employee.user_id.partner_id.id)
            if employee.parent_id.user_id:
                partner.append(employee.parent_id.user_id.partner_id.id)
        # channel_id=self.env.ref('slnee_hr.manager_channel').id
        self.message_subscribe(partner_ids=partner)
        return super(HrAdminCopyCenter, self).write(value)

    @api.multi
    def unlink(self):
        """
            Delete existing record.
            :return: Current Delete record ID
        """
        for rec in self:
            if rec.state in ['confirm', 'in_progress', 'validate', 'done', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % (rec.state))
        return super(HrAdminCopyCenter, self).unlink()

    @api.multi
    def action_confirm(self):
        """
            sent the status of generating record in confirm state
        """
        self.ensure_one()
        self.message_post(message_type="email", subtype='mail.mt_comment', body='Request For Copy Confirmed.')
        self.state = 'confirm'

    @api.multi
    def action_inprogress(self):
        """
            sent the status of generating record in in progress state
        """
        self.ensure_one()
        self.message_post(message_type="email", subtype='mail.mt_comment', body='Request For Copy Is In Progress.')
        self.state = 'in_progress'

    @api.multi
    def action_refuse(self):
        """
            sent the status of generating record in refuse state
        """
        self.ensure_one()
        self.message_post(message_type="email", subtype='mail.mt_comment', body='Request For Copy Refused.')
        self.state = 'refuse'

    @api.multi
    def action_set_draft(self):
        """
            sent the status of generating record in draft state
        """
        self.ensure_one()
        self.message_post(message_type="email", subtype='mail.mt_comment', body='Request For Copy Set To Draft.')
        self.state = 'draft'

    @api.multi
    def action_done(self):
        """
            sent the status of generating record in done state
        """
        self.ensure_one()
        self.message_post(message_type="email", subtype='mail.mt_comment', body='Request For Copy Is Done.')
        self.write({'state': 'done', 'expense_total': self.amount_total})

    @api.multi
    def action_validate(self):
        """
            sent the status of generating record in validate state
        """
        self.ensure_one()
        admin_groups_config_obj = self.env['hr.groups.configuration']
        admin_groups_config_ids = admin_groups_config_obj.search([('branch_id', '=', self.employee_id.branch_id.id), ('admin_ids', '!=', False)])
        admin_groups_ids = admin_groups_config_ids and admin_groups_config_ids[0]
        user_ids = admin_groups_ids and [employee.user_id.id for employee in admin_groups_ids.admin_ids if employee.user_id] or []
        self.sudo().message_subscribe_users(user_ids=user_ids)
        self.message_post(message_type="email", subtype='mail.mt_comment', body='Request For Copy Is Approved.')
        return self.write({'state': 'validate', 'approved_by': self.env.user.id, 'approved_date': datetime.today()})

    @api.onchange('date_required')
    def onchange_date_required(self):
        """
            onchange the value based on selected date required,
            return: warning
        """
        warning = {}
        if self.date_required and self.date_required < self.date_submited:
            warning.update({'title': _('Information'),
                           'message': _("Require Date must be greater than Submit Date.")})
            self.date_required = False
        return {'warning': warning}

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange the value based on selected employee,
            job, department, company, email, mobile
        """
        self.job_id = False
        self.department_id = False
        self.company_id = False
        self.email_contact = False
        self.mobile_contact = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            self.email_contact = self.employee_id.work_email
            self.mobile_contact = self.employee_id.mobile_phone

    @api.multi
    def generate_expense(self):
        """
            Generate expense of employee.
            return: Generated expense ID
        """
        self.ensure_one()
        product_id = self.env.ref('slnee_hr_copy_center.copy_center')
        name = 'Copy Center - ' + self.employee_id.name
        return self.generate_expense_payment(self, self.special_instructions, self.emp_contribution, self.company_contribution, self.payment_mode, name, product_id, self.expense_total)

    @api.multi
    def view_expense(self):
        """
            Redirect to view expense method.
            return: Current expense record ID
        """
        for line in self:
            return self.redirect_to_expense(line.expense_ids)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = 'id desc'

    stationary = fields.Boolean(string='Stationary')

class ProductLine(models.Model):
    _name = 'product.line'
    _order = 'id desc'

    @api.multi
    def _amount_calculate(self):
        """
            Calculate subtotal price.
        """
        for line in self:
            line.price_subtotal += (line.set * line.quantity * line.price_unit)

    copy_center_id = fields.Many2one('copy.center', string="Copy Center")
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Paper Per Set', required=True, default=1)
    set = fields.Float(string='Sets', required=True, default=1)
    price_unit = fields.Float(string='Unit Price', required=True)
    price_subtotal = fields.Float(compute=_amount_calculate, string="Amount")

    @api.onchange('product_id')
    def onchange_product(self):
        """
            onchange the value based on selected product,
            description, price unit
        """
        self.description = False
        self.price_unit = False
        if self.product_id:
            self.description = self.product_id.description_sale
            self.price_unit = self.product_id.list_price
