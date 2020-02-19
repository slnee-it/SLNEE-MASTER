# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HRContract(models.Model):
    _name = 'hr.contract'
    _inherit = ['mail.thread', 'hr.contract']

    mobile = fields.Boolean('Allow Mobile Allowance')
    mobile_allowance = fields.Float('Mobile Allowance', help="Mobile Allowance")
    signon_bonus = fields.Boolean('Sign on Bonus')
    signon_bonus_amount = fields.Float('Bonus Amount', digits=(16, 2), help="Mention the Sign on Bonus amount.")
    period_ids = fields.Many2many('year.period', string='Month(s)',
                                    help='Specify month(s) in which the sign on bonus will be distributed. Bonus will be distributed in Bonus Amount/Number of Month(s).')
    #iron_allowance = fields.Float('Iron Allowance', digits=(16, 2), help="Mention the iron allowance.")
    #is_iron_allowance = fields.Boolean('Allow Iron Allowance')
    notice_start_date = fields.Date('Notice Start Date', readonly=True)
    notice_end_date = fields.Date('Notice End Date', readonly=True)
    is_leaving = fields.Boolean('Leaving Notice')
    # is_notify = fields.Boolean('is notify ? ')
    # notify_date = fields.Date("Notify Date", compute='_get_notify_date')
    basic = fields.Float('Basic', compute='_get_amount', help='Basic Salary of Employee(value after gross/1.35)')
    HRA = fields.Float(string='House Rent Allowance', compute='_get_amount', help="HRA of employee (25% of basic)")
    TA = fields.Float(string='Transport Allowance', compute='_get_amount', help="Transport Allowance of employee (10% of Basic)")

    @api.model
    def create(self, values):
        """
            create a new record
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id or False})
        return super(HRContract, self).create(values)

    @api.multi
    def write(self, values):
        """
            update an existing record
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id or False})
        return super(HRContract, self).write(values)

    # @api.one
    # @api.depends('date_end')
    # def _get_notify_date(self):
    #     self.notify_date = False
    #     if self.date_end:
    #         date_end = fields.Datetime.from_string(self.date_end)
    #         self.notify_date = date_end - relativedelta(months=+2)

    @api.multi
    @api.depends('wage')
    def _get_amount(self):
        """
            set the values of Basic, HRA, TA if wage is greater than 0.
        """
        for contract in self:
            if contract.wage > 0:
                contract.basic = contract.wage / 1.35
                contract.HRA = contract.basic * 0.25
                contract.TA = contract.basic * 0.1

    #===========================================================================
    # Removed code due to not accurance based on _get_total_members
    # _sql_constraints = [
    #     ('check_adults', 'CHECK(adults >= 1 and adults <= 2)', 'Number of adults must be greater than 0 and less then 3!'),
    #     ('check_childs', 'CHECK(children<=2)', 'Maximum allowed number of children are two!'),
    # ]
    #===========================================================================

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            set the code, job, department select on employee.
        """
        self.job_id = False
        self.mobile_allowance = 0.0
        if self.employee_id:
            employee = self.env['hr.employee'].browse(self.employee_id.id)
            if employee.grade_id:
                self.mobile_allowance = employee.grade_id.mobile_allowance
            self.job_id = employee.job_id.id or False
            self.department_id = employee.department_id.id or False

    @api.onchange('mobile', 'employee_id')
    def onchange_mobile(self):
        """
            Check the mobile allowance in employee record
        """
        self.mobile_allowance = 0.0
        if self.mobile and self.employee_id:
            employee = self.env['hr.employee'].browse(self.employee_id.id)
            if employee.grade_id:
                self.mobile_allowance = employee.grade_id.mobile_allowance

    # @api.onchange('is_iron_allowance')
    # def onchange_iron_allowance(self):
    #     """
    #         Iron allowance
    #     """
    #     self.iron_allowance = 0.0
    #     if self.is_iron_allowance:
    #         self.iron_allowance = 130.0

    @api.model
    def run_scheduler(self):
        """
            sent an email with notification of contract state, automatically sent an email to the client.
        """
        contract_ids = self.search([('state', 'in', ['draft', 'open'])])
        try:
            template_id = self.env.ref('hr_contract.email_template_hr_contract_notify')
        except ValueError:
            template_id = False
        hr_groups_config_obj = self.env['hr.groups.configuration']
        for contract in contract_ids:
            if contract.date_end:
                if str(datetime.now().date()) == str((datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=+2)).date()):
                    hr_groups_config_ids = hr_groups_config_obj.search([('branch_id', '=', contract.employee_id.branch_id.id or False), ('hr_ids', '!=', False)])
                    hr_groups_ids = hr_groups_config_ids and hr_groups_config_obj.browse(hr_groups_config_ids.ids)[0]
                    user_ids = hr_groups_ids and [item.user_id.id for item in hr_groups_ids.hr_ids if item.user_id] or []
                    email_to = ''
                    res_users_obj = self.env['res.users']
                    for user_id in res_users_obj.browse(user_ids):
                        if user_id.email:
                            email_to = email_to and email_to + ',' + user_id.email or email_to + user_id.email
                    template_id.write({'email_to': email_to, 'reply_to': email_to, 'auto_delete': False})
                    template_id.send_mail(contract.id, force_send=True)
                    contract.write({'state': 'pending'})
                elif datetime.now().date() == datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT).date():
                    contract.write({'state': 'close'})
        return True


class HRGrade(models.Model):
    _inherit = "hr.grade"

    mobile_allowance = fields.Float('Mobile Allowance', help="Mobile Allowance")
