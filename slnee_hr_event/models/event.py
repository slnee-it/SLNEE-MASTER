# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class EventEvent(models.Model):
    _inherit = 'event.event'

    @api.one
    @api.depends('registration_ids.user_id', 'registration_ids.state')
    def _compute_subscribe(self):
        """ Determine whether the current user is already subscribed to any event in `self` """
        self.is_subscribed = False
        self.is_subscribed = any(
            reg.user_id == self.env.user and reg.state in ('draft', 'open', 'done')
            for reg in self.registration_ids
        )

    cost = fields.Float('Training Cost')
    approve_hof = fields.Boolean('Approval of Head of Function')
    target = fields.Selection([('office', 'Office Wise'), ('department', 'Department Wise'), ('job', 'Job Profile Wise')], string="Target Group")
    department_ids = fields.Many2many('hr.department', 'department_event_rel', 'event_id', 'department_id', string="Departments")
    branch_ids = fields.Many2many('hr.branch', 'branch_event_rel', 'event_id', 'branch_id', string="Offices")
    job_ids = fields.Many2many('hr.job', 'job_event_rel', 'event_id', 'job_id', string="Job Profiles")
    is_subscribed = fields.Boolean(compute="_compute_subscribe", string='Subscribed')
    # email_confirmation_id =  fields.Many2one('email.template','Training Confirmation Email', help="If you set an email template, each participant will receive this email announcing the confirmation of the training.")
    employee_ids = fields.Many2many('hr.employee', 'event_event_hr_employee_rel', 'event_event_id', 'hr_employee_id', string='Employees')
    total_hours = fields.Float('Total Hours', default="0.0")

    @api.multi
    def unlink(self):
        for event_id in self:
            if len(event_id.registration_ids) > 0:
                raise UserError(_('You cannot delete an events because already employee(s) registered.'))
        return super(EventEvent, self).unlink()

    # Not available in v11
    # @api.multi
    # def subscribe_to_event(self):
    #     """ Subscribe the current user to a given event """
    #     self.ensure_one()
    #     user = self.env.user
    #     num_of_seats = int(self._context.get('ticket', 1))
    #     regs = self.registration_ids.filtered(lambda reg: reg.user_id == user)
    #     # the subscription is done as SUPERUSER_ID because in case we share the
    #     # kanban view, we want anyone to be able to subscribe
    #     employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
    #     if employee:
    #         if not regs:
    #             regs = regs.sudo().create({
    #                 'event_id': self.id,
    #                 'employee_id': employee.id,
    #                 'email': employee.work_email,
    #                 'name': employee.name,
    #                 'phone': employee.mobile_phone,
    #                 'user_id': user.id,
    #                 'nb_register': num_of_seats,
    #             })
    #         else:
    #             regs.write({'nb_register': num_of_seats})
    #     # regs.sudo().confirm_registration()

    def get_mail_url(self, employee):
        config_ids = self.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')])
        employee_id = self.env['event.registration'].search([('employee_id', '=', employee.id),('event_id', '=', self.id)], limit=1)
        if config_ids:
            name = "Event"
            url = config_ids[0].value + '/web#id=' + str(employee_id.id) + '&view_type=form&model=event.registration'
            return url

    @api.multi
    def action_send_mail(self, employee):
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('slnee_hr_event', 'email_template_event_confirm')[1]
        except ValueError:
            template_id = False
        if template_id:
            template = self.env['mail.template'].browse(template_id)
            template.with_context({'employee':employee}).send_mail(self.id, force_send=True,raise_exception=False,email_values=None)

    @api.one
    def button_draft(self):
        """
            Change state to draft.
        """
        self.target = False
        self.branch_ids = False
        self.department_ids = False
        self.job_ids = False
        self.employee_ids = False
        return super(EventEvent, self).button_draft()

    @api.one
    def button_confirm(self):
        """
            Change state to confirm and check seats.
        """
        record_list = []
        for employee in self.employee_ids:
            attendee = {
                'employee_id':employee.id,
                'event_id': self.id,
            }
            record_list.append(self.env['event.registration'].create(attendee))
            if employee.user_id:
                self.action_send_mail(employee)
            event = self.event_mail_ids.filtered(lambda r: r.template_id.id == self.env.ref('event.event_reminder').id)
            if not event:
                self.event_mail_ids = self.env['event.mail'].create({'template_id':self.env.ref('event.event_reminder').id,
                                                'event_id':self.id,
                                                'interval_unit':'hours',
                                                'interval_type':'before_event',
                                        })
        for rec in record_list:
            event_registration = self.event_mail_ids.mail_registration_ids.filtered(lambda r: r.registration_id.employee_id == rec.employee_id)
            if not event_registration:
                self.event_mail_ids.write({
                    'mail_registration_ids':[(0, 0,{'registration_id':rec.id,
                                            'schedular_id':self.id,
                                            })]
                })
        lst_registered_emp = [registered_emp.id for registered_emp in self.registration_ids if registered_emp.state == 'open']
        if self.seats_min <= len(lst_registered_emp) and self.seats_max >= len(lst_registered_emp):
            return super(EventEvent, self).button_confirm()
        else:
            raise UserError(_('The total of confirmed registration for the event `%s` does not meet the expected minimum/maximum. Please reconsider those limits before going further.') % (self.name))

    @api.one
    def button_done(self):
        """
            Change state to done and check dates.
        """
        if self.date_begin < fields.Datetime.now():
            return super(EventEvent, self).button_done()
        else:
            raise UserError(_('You can\'t finish training, because Starting Date of training is %s') % (self.date_begin))

    @api.onchange('target', 'branch_ids', 'department_ids', 'job_ids')
    def onchange_target(self):
        """
            Set employee according to target, branch, department and job.
        """
        domain = [('active', '=', True)]
        if self.target == 'office':
            domain.append(('branch_id', 'in', self.branch_ids.ids))
        elif self.target == 'department':
            domain.append(('department_id', 'in', self.department_ids.ids))
        elif self.target == 'job':
            domain.append(('job_id', 'in', self.job_ids.ids))
        if self.target:
            employee = self.env["hr.employee"].search(domain)
            self.employee_ids = employee.ids


class EventRegistration(models.Model):
    _name = 'event.registration'
    _inherit = ['event.registration', 'hr.expense.payment']

    @api.one
    def _employee_contribution(self):
        """
            Calculate employee contribution for event.
        """
        self.emp_contribution = self.expense_total - self.company_contribution

    employee_id = fields.Many2one('hr.employee', 'Employee', default=lambda self: self.env['hr.employee'].get_employee())
    expense_total = fields.Float('Total Expense')
    company_contribution = fields.Float('Company Contribution')
    emp_contribution = fields.Float(compute=_employee_contribution, string='Employee Contribution')
    expense_id = fields.Many2one('hr.expense', 'Expense')
    expense_note = fields.Text('Expense Note')
    #event_id = fields.Many2one('event.event', 'Training', required=True, readonly=True, states={'draft': [('readonly', False)]})
    # ADD in v9
    user_id = fields.Many2one('res.users', string='User', states={'done': [('readonly', True)]})
    expense_ids = fields.Many2many('hr.expense', string="Expenses", copy=False)

    @api.multi
    def generate_expense(self):
        """
            Generate expense of employee.
            return: Generated expense ID
        """
        self.ensure_one()
        product_id = self.env.ref('slnee_hr_event.training_exp')
        name = 'Training Registration - ' + self.employee_id.name
        return self.generate_expense_payment(self, self.expense_note, self.emp_contribution, self.company_contribution, self.payment_mode, name, product_id, self.expense_total)

    @api.multi
    def view_expense(self):
        """
            Redirect to view expense method.
            return: Current expense record ID
        """
        for line in self:
            return self.redirect_to_expense(line.expense_ids)

    @api.onchange('event_id')
    def onchange_event_id(self):
        """
            Set total expense according to total.
        """
        if self.event_id:
            self.expense_total = self.event_id.cost

    @api.multi
    @api.depends('event_id')
    def name_get(self):
        res = []
        for rec in self:
            if rec.event_id:
                name = rec.employee_id.name +',' +rec.event_id.name or ''
                res.append((rec.id, name))
        return res

    @api.one
    def action_send_mail(self):
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.user.id == self.event_id.user_id.id:
                template_id = ir_model_data.get_object_reference('slnee_hr_event', 'slnee_hr_event_subscription')[1]
            else:
                template_id = ir_model_data.get_object_reference('slnee_hr_event', 'email_template_event_registration_confirm_by_attendee')[1]
        except ValueError:
            template_id = False
        if template_id:
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True,raise_exception=False,email_values=None)

    @api.one
    def confirm_registration(self):
        super(EventRegistration, self).confirm_registration()
        self.action_send_mail()

    @api.one
    def registration_cancel_mail(self):
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.user.id == self.event_id.user_id.id:
                template_id = ir_model_data.get_object_reference('slnee_hr_event', 'email_template_event_registration_cancel_by_responsible_user')[1]
            else:
                template_id = ir_model_data.get_object_reference('slnee_hr_event', 'email_template_event_registration_cancel_by_attendee')[1]
        except ValueError:
            template_id = False
        if template_id:
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True,raise_exception=False,email_values=None)

    @api.one
    def button_reg_cancel(self):
        super(EventRegistration, self).button_reg_cancel()
        self.registration_cancel_mail()


    @api.one
    def button_reg_close(self):
        super(EventRegistration, self).button_reg_close()
        if self.state == 'done' and self.date_closed and self.employee_id:
            self.env['hr.employee.training'].create({
                'employee_id': self.employee_id.id,
                'name': self.event_id.name,
                'state': 'validate',
                'start_date': self.event_id.date_begin ,
                'end_date': self.event_id.date_end,
                'type': 'internal',
                'total_hours': self.event_id.total_hours,
                'category': self.event_id.event_type_id.id
            })

    @api.multi
    def mass_mail_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
       '''
        self.ensure_one()
        if len(self.ids) == 10:
            return False
        try:
            template_id = self.env.ref('slnee_hr_event.email_template_event').id
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context)
        email_recipients = []
        for obj in self:
            if obj.employee_id:
                if obj.employee_id.parent_id and obj.employee_id.parent_id.user_id:
                    email_recipients.append(obj.employee_id.parent_id.user_id.partner_id.id)
                if obj.event_id.approve_hof and obj.employee_id.coach_id and obj.employee_id.coach_id.user_id:
                    email_recipients.append(obj.employee_id.coach_id.user_id.partner_id.id)

        ctx.update({
            'default_model': 'event.registration',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_partner_ids': list(set(email_recipients)),
            'default_type': 'email',
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

    @api.multi
    def mail_send(self):
        """
            This function opens a window to compose an email, with the edi sale template message loaded by default
        """
        self.ensure_one()
        assert len(self.ids) == 1, 'This option should only be used for a single id at a time.'
        try:
            template_id = self.env.ref('slnee_hr_event', 'email_template_event').id
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref('mail', 'email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context)
        email_recipients = []
        registration = self
        if registration.employee_id:
            if registration.event_id.approve_hof and registration.employee_id.coach_id and registration.employee_id.parent_id.user_id:
                email_recipients.append(registration.employee_id.coach_id.user_id.partner_id.id)
            if registration.employee_id.parent_id and registration.employee_id.parent_id.user_id:
                email_recipients.append(registration.employee_id.parent_id.user_id.partner_id.id)

        ctx.update({
            'default_model': 'event.registration',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_partner_ids': list(set(email_recipients)),
            'default_type': 'email',
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
