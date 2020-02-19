# -*- coding: utf-8 -*-

from openerp.report import report_sxw
import arabic_reshaper
from bidi.algorithm import get_display

def get_arabic_string(string):
    reshaped_text = arabic_reshaper.reshape(string)
    bidi_text = get_display(reshaped_text)
    return bidi_text

class graduate_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(graduate_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_arabic_string': get_arabic_string,
            'get_data': self.get_data,
            'get_passport_nationalId_details': self.get_passport_nationalId_details,
        })

    def get_data(self, data):
        final_list = []
        values = {'report_name': ''}
        if data['form']['report_name']:
            contract = self.env['hr.contract'].browse(data['form']['ids'][0])
            values.update({'report_name': data['form']['report_name'][0]['report_name']})
            values['contract'] = contract
        final_list.append(values)
        return final_list

    def get_passport_nationalId_details(self, employee_id):
        final_result = []
        employee_pool = self.env['hr.employee']
        contract_pool = self.env['hr.contract']

        if employee_id:
            emp = employee_pool.browse(employee_id)
            values = {'doc_number': '', 'emp_title': '', 'branch_id': '', 'job_id': '', 'issue_date': '', 'issue_place': '', 'country_id': '', 'emp_name': ''}
            values['emp_name'] = emp
            values['emp_title'] = emp.title and emp.title.name or ''
            values['job'] = emp.job_id  or ''
            values['department'] = emp.department_id  or ''
            values['branch'] = emp.branch_id  or ''
            values['grade_id'] = emp.grade_id.name or ''
            values['emp_city'] = emp.address_home_id.city or ''
            values['emp_contry'] = emp.address_home_id.country_id or ''
            values['join_date'] = emp.date_of_join or ''

            contract_ids = contract_pool.search([('employee_id', '=', emp.id)])
            values['wage'] = ''
            values['basic'] = ''
            values['HRA'] = ''
            values['TA'] = ''

            if contract_ids:
                contract_id = contract_pool.browse(contract_ids[0])
                values['wage'] = contract_id.wage or ''
                values['basic'] = contract_id.basic or ''
                values['HRA'] = contract_id.HRA or ''
                values['TA'] = contract_id.TA or ''

            # if manager_id:
            #     manager = employee_pool.browse(self.cr, self.uid, manager_id)
            #     values['manager'] = manager.name or ''
            #     values['auth_job_id'] = manager.job_id and manager.job_id.name or ''

            if emp.country_id:
                values['country_id'] = emp.country_id
            for doc in emp.document_ids:
                if doc.type_id.code == 'pno' and emp.country_id.code != 'SA':  # passport
                    values['doc_number'] = doc.doc_number
                    values['issue_date'] = doc.issue_date
                    values['issue_place'] = doc.issue_place
                elif doc.type_id.code == 'nid' and emp.country_id.code == 'SA':  # national
                    values['doc_number'] = doc.doc_number
                    values['issue_date'] = doc.issue_date
                    values['issue_place'] = doc.issue_place

            final_result.append(values)
        return final_result
report_sxw.report_sxw('report.graduate.report', 'hr.contract', 'addons/slnee_hr_letters/report/graduate_report.rml', parser=graduate_report)
