# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    gosi_ids = fields.Many2one('employee.gosi', 'GOSI NO')


class EmployeeGosi(models.Model):
    _name = 'employee.gosi'
    _description = "Employee GOSI"
    _rec_name = 'gosi_no'
    _inherit = 'mail.thread'

    region_type = fields.Selection([('saudi', 'Saudi'), ('non-saudi', 'Non-Saudi')], string='Type',
                                   compute='_set_region_type', store=True)
    iqama_no = fields.Char('Iqama No')
    employee_id = fields.Many2one('hr.employee', required=True, string='Employee')
    job_id = fields.Many2one('hr.job', readonly=True, string='Job Position')
    passport_no = fields.Char('Passport No', readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    gosi_no = fields.Char('GOSI No', required=True, copy=False)
    issue_date = fields.Date('Issue Date', required=False, default=date.today().strftime('%Y-%m-%d'))
    birth_date = fields.Date('Date of Birth', readonly=True)
    hijri_birth_date = fields.Char('Date of Birth(Hijri)')
    country_id = fields.Many2one('res.country', 'Nationality', readonly=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)
    payslip_line_ids = fields.One2many('gosi.payslip.line', 'gosi_id', string='Payslip Lines', copy=False)
    hadaf_line_ids = fields.One2many('hadaf.payslip.line', 'hadaf_id', string='HADAF Lines', copy=False)
    calculate_hadaf = fields.Boolean("Hide Password")

    _sql_constraints = [
        ('gosi_unique', 'unique(gosi_no)', 'GOSI Number is already exists !'),
        ('employee_unique', 'unique(employee_id)', 'Same employee record is already exists.'),
    ]

    @api.depends('employee_id')
    @api.multi
    def _set_region_type(self):
        for rec in self:
            rec.region_type = 'saudi' if rec.employee_id.country_id.code == 'SA' else 'non-saudi'

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
            onchange details of employee based on selecting employee
            employee code, job, department, birth date, country, gosi no, etc.
        """
        self.job_id = False
        self.birth_date = False
        self.department_id = False
        self.country_id = False
        self.gosi_no = False
        self.passport_no = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.passport_no = self.employee_id.passport_id
            self.birth_date = self.employee_id.birthday
            self.department_id = self.employee_id.department_id.id
            self.country_id = self.employee_id.country_id.id
            self.gosi_no = self.employee_id.gosi_ids.gosi_no
            self.company_id = self.employee_id.company_id.id

    @api.model
    def create(self, values):
        """
            Create a new record
            :return: Newly created record ID
        """
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id,
                           'department_id': employee.department_id.id,
                           'country_id': employee.country_id.id,
                           'birth_date': employee.birthday,
                           'passport_no': employee.passport_id,
            })
        res = super(EmployeeGosi, self).create(values)
        return res

    @api.multi
    def write(self, values):
        """
            Update an existing record.
            :param values: Current record fields data
            :return: Current update record ID
        """
        if values.get('employee_id'):
            employee = self.env['hr.employee'].browse(values['employee_id'])
            values.update({'job_id': employee.job_id.id,
                           'country_id': employee.country_id.id,
                           'department_id': employee.department_id.id,
                           'birth_date': employee.birthday,
                           'passport_no': employee.passport_id,
                         })
        return super(EmployeeGosi, self).write(values)

    @api.multi
    @api.depends('employee_id', 'gosi_no')
    def name_get(self):
        """
            return the name `Name, (Gosi No)`
        """
        res = []
        for gosi in self:
            if gosi.employee_id:
                name = ''.join([gosi.employee_id.name, '(', gosi.gosi_no, ')'])
            res.append((gosi.id, name))
        return res


class GosiPayslipLine(models.Model):
    _name = 'gosi.payslip.line'
    _description = "GOSI Payslip Line"
    _order = 'id desc'

    gosi_id = fields.Many2one('employee.gosi', 'GOSI', required=True, ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, ondelete="cascade")
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', required=True, ondelete="cascade")
    date = fields.Date('Date', required=True)
    amount = fields.Float('GOSI Amount', required=True)


class HadafPayslipLine(models.Model):
    _name = 'hadaf.payslip.line'
    _description = "HADAF Payslip Line"
    _order = 'id desc'

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, ondelete="cascade")
    date = fields.Date('Date', required=True)
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', required=True, ondelete="cascade")
    amount = fields.Float('GOSI Amount', required=True)
    hadaf_id = fields.Many2one('employee.gosi', ondelete="cascade")
