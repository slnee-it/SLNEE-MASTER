# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo.addons.slnee_hr_letters.report import calverter
from odoo import fields, models, api, _
from odoo.exceptions import UserError


def get_arabic_string(string):
    reshaped_text = arabic_reshaper.reshape(string)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def get_islamic_date(date):
    date = str(date)
    date_list = str(date).split('-')
    cal = calverter.Calverter()
    jd = cal.gregorian_to_jd(int(date_list[0]), int(date_list[1]), int(date_list[2]))
    islamic_date = cal.jd_to_islamic(jd)
    islamic_date_format = str(islamic_date[0]) + "-" + str(islamic_date[1]) + "-" + str(islamic_date[2])
    return islamic_date_format

class BankloanTransfer(models.AbstractModel):
    _name = 'report.slnee_hr_letters.bankloan_transfer_qweb'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id.id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''
            values['wage'] = ''
            values['HRA'] = ''
            values['TA'] = ''
            if contract_ids:
                contract_id = contract_ids[0]
                values['wage'] = contract_id.wage or ''
                values['HRA'] = contract_id.HRA or ''
                values['TA'] = contract_id.TA or ''
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''

        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class BankloanTransferFemale(models.AbstractModel):
    _name = 'report.slnee_hr_letters.bankloan_transfer_female_qweb'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or  ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''
            values['wage'] = ''
            values['HRA'] = ''
            values['TA'] = ''
            if contract_ids:
                contract_id = contract_ids[0]
                values['wage'] = contract_id.wage or ''
                values['HRA'] = contract_id.HRA or ''
                values['TA'] = contract_id.TA or ''
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''

        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class BankopenAcoount(models.AbstractModel):
    _name = 'report.slnee_hr_letters.bankopen_account_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or  ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''

        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def render_html(self, docids, data=None):
        Report = self.env['report']
        report_obj = Report._get_report_from_name('slnee_hr_letters.bankopen_account_report')
        report = self.env['multi.reports'].browse(data['id'])
        docargs = {
            'doc_ids': self.ids,
            'doc_model':  report_obj.model,
            'docs': report,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }
        return Report.render('slnee_hr_letters.bankopen_account_report', docargs)

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class BankopenAccountFemale(models.AbstractModel):
    _name = 'report.slnee_hr_letters.bankopen_account_report_female'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or  ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''

        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class CertiApproval(models.AbstractModel):
    _name = 'report.slnee_hr_letters.certificate_toapprove'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        # contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            # contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class FamilyIqama(models.AbstractModel):
    _name = 'report.slnee_hr_letters.family_iqama_report'

    def get_data(self, data):
        # doc_type_obj = self.env['res.document.type']
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

        values = {'iqama_no': ''}
        if data['employee_id']:
            # emp = employee_obj.browse(data['employee_id'][0])
            # doc_type_id = doc_type_obj.search([('code', '=', 'ino')])  # iqama
            if employee.document_ids:
                for doc_id in employee.document_ids:
                    if doc_id.type_id.code == 'ino':  # iqama
                        values.update({'iqama_no': doc_id.doc_number})
        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class MroorReport(models.AbstractModel):
    _name = 'report.slnee_hr_letters.mroor_qreport'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        # contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            # contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['leave_date'] = employee.date_of_leave
        values['job'] = employee.job_id.arabic_name or ''
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class HouseAllowance(models.AbstractModel):
    _name = 'report.slnee_hr_letters.house_allowance_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        # contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            # contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }

class WhomeConcern(models.AbstractModel):
    _name = 'report.slnee_hr_letters.whomeconcern_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['employee'] = employee
        values['emp_title'] = employee.title.name or ''
        values['date'] = data['date']
        values['job_id'] = employee.job_id.name or ''
        values['gender'] = 'His' if employee.gender == 'male' else 'Her'
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.name or ''
        values['department'] = employee.department_id.name or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = ''.join([manager.name or '', manager.middle_name or '', manager.last_name or ''])
            values['auth_job_id'] = manager.job_id.name or ''

        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class TowhomeConcern(models.AbstractModel):
    _name = 'report.slnee_hr_letters.towhome_concern_arabic_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        # values['wage'] = ''
        # if contract_ids:
        #     contract_id = contract_obj.browse(contract_ids[0])
        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class TowhomConcernFemale(models.AbstractModel):
    _name = 'report.slnee_hr_letters.towhom_concern_female_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class StampingCertificate(models.AbstractModel):
    _name = 'report.slnee_hr_letters.stamping_certificate_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            # contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class StampingCertificateFemale(models.AbstractModel):
    _name = 'report.slnee_hr_letters.stamping_certificate_female_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        # contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            # contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or  ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class WifefromHomeCountry(models.AbstractModel):
    _name = 'report.slnee_hr_letters.wifefrom_home_country_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])

        contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

        values = {'iqama_no': ''}
        if data['employee_id']:
            # emp = employee_obj.browse(data['employee_id'][0])
            # doc_type_id = doc_type_obj.search([('code', '=', 'ino')])  # iqama
            if employee.document_ids:
                for doc_id in employee.document_ids:
                    if doc_id.type_id.code == 'ino':  # iqama
                        values.update({'iqama_no': doc_id.doc_number})

        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class WalidSchool(models.AbstractModel):
    _name = 'report.slnee_hr_letters.walid_school_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''

        values['wage'] = contract_ids[0].wage if contract_ids else ''
        values['employee'] = employee
        values['emp_title'] = employee.title.name or ''
        values['date'] = data['date']
        values['job_id'] = employee.job_id.name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.name or ''
        values['department'] = employee.department_id.name or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = ''.join([manager.name or '', manager.middle_name or '', manager.last_name or ''])
            values['auth_job_id'] = manager.job_id.name or ''

        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class SaudibritishBankloan(models.AbstractModel):
    _name = 'report.slnee_hr_letters.saudibritish_bankloan_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        final_result = []
        values = {}
        values['doc_number'] = ''
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            values['employee'] = employee
            contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

            if employee.country_id:
                values['country_id'] = employee.country_id or ''
            for doc in employee.document_ids:
                if doc.type_id.code == 'ino' and employee.country_id.code != 'SA':  # iqama
                    values['doc_number'] = doc.doc_number or ''
                elif doc.type_id.code == 'nid' and employee.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number or ''
            values['wage'] = ''
            values['HRA'] = ''
            values['TA'] = ''
            values['leave_date'] = ''
            if contract_ids:
                contract_id = contract_ids[0]
                values['wage'] = contract_id.wage or ''
                values['HRA'] = contract_id.HRA or ''
                values['TA'] = contract_id.TA or ''
                values['leave_date'] = contract_id.date_end or ''
        values['employee'] = employee
        values['emp_staf'] = employee.code or ''
        values['date'] = data['date']
        values['emp_title'] = employee.title.name or ''
        values['job_id'] = employee.job_id.name or ''
        values['branch_id'] = employee.branch_id.name or ''
        values['join_date'] = employee.date_of_join or ''
        values['emp_country'] = employee.country_id.name or ''
        values['department'] = employee.department_id.name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = ' '.join([manager.name or '', manager.middle_name or '', manager.last_name or ''])
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }


class Transport(models.AbstractModel):
    _name = 'report.slnee_hr_letters.slnee_hr_letters_transport_report'

    def get_data(self, data):
        employee_obj = self.env['hr.employee']
        # contract_obj = self.env['hr.contract']
        final_result = []
        if data['employee_id']:
            employee = employee_obj.browse(data['employee_id'][0])
            # contract_ids = contract_obj.search([('employee_id', '=', employee.id)])

        values = {'iqama_no': ''}
        if data['employee_id']:
            # emp = employee_obj.browse(data['employee_id'][0])
            # doc_type_id = doc_type_obj.search([('code', '=', 'ino')])  # iqama
            if employee.document_ids:
                for doc_id in employee.document_ids:
                    if doc_id.type_id.code == 'ino':  # iqama
                        values.update({'iqama_no': doc_id.doc_number})

        values['employee'] = employee
        values['date'] = data['date']
        values['job_id'] = employee.job_id.arabic_name or ''
        values['branch_id'] = employee.branch_id.arabic_name or ''
        values['join_date'] = employee.date_of_join
        values['emp_country'] = employee.country_id.arabic_country_name or ''
        values['department'] = employee.department_id.arabic_name or ''
        values['account_no'] = employee.bank_account_id.acc_number or ''
        if data['manager_id']:
            manager = employee_obj.browse(data['manager_id'][0])
            values['manager'] = manager.arabic_name or ''
            values['auth_job_id'] = manager.job_id.arabic_name or ''
        final_result.append(values)
        return final_result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_arabic_string': get_arabic_string,
            'get_islamic_date': get_islamic_date,
            'get_data': self.get_data(data),
        }
