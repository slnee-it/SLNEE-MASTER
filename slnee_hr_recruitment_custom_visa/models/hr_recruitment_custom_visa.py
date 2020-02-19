# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import date, datetime
from dateutil import relativedelta


class HrRecruitmentCustomVisa(models.Model):
    _inherit = 'hr.applicant'

    @api.multi
    def processed_visa(self):
        """
            Used for visa proceed
            return: visa form on wizard
        """
        visa_obj = self.env['hr.employee.rec.visa']
        for applicant in self:
            form_view = self.env.ref('slnee_hr_visa_recruiter.hr_employee_rec_visa_form')
            tree_view = self.env.ref('slnee_hr_visa_recruiter.hr_employee_rec_visa_tree')
            new_visa_id = visa_obj.create({
                'job_id': applicant.job_id and applicant.job_id.id,
                'employee_id': applicant.emp_id and applicant.emp_id.id,
                'email': applicant.email_from,
                'visa_for': 'individual',
                'reason_of_visa': 'new_join_employee',
                'fiscal_year_id': 1,
                'request_by_id': self.env.uid,
                'country_id': applicant.country_id and applicant.country_id.id or '',
                'requested_date_from': date.today().strftime('%Y-%m-%d'),
                'requested_date_to': str(datetime.now() + relativedelta.relativedelta(months=+3, day=1, days=-1))[:10],
            })
        return {'view_type': 'form',
                'view_mode': 'tree, form',
                'res_model': 'hr.employee.rec.visa',
                'view_id': False,
                'views': [(form_view.id, 'form'),
                          (tree_view.id, 'tree')],
                'type': 'ir.actions.act_window',
                'res_id': new_visa_id.id,
                'target': 'current',
                'nodestroy': True}
