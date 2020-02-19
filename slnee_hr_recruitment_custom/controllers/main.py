# -*- coding: utf-8 -*-

import logging
import odoo.addons.survey
from odoo.addons.survey.controllers.main import *

from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF, ustr
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class WebsiteSurvey(WebsiteSurvey):

    # Survey start
    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def start_survey(self, survey, token=None, **post):
        super_res = super(WebsiteSurvey, self).start_survey(survey, token, **post)
        cr = request.cr
        cr.execute('SELECT id FROM survey_user_input ORDER BY id DESC LIMIT 1')
        user_input_id = cr.fetchone()[0]

        clearance_obj = request.env['hr.employee.clearance']
        clearance_context = clearance_obj.context_data()
        if clearance_context:
            model = clearance_context and clearance_context.get('object', False)
            if model == 'hr.employee.clearance':
                if clearance_context.get('active_ids', False):
                    employee_clearance_id = clearance_context.get('active_ids', False)[0]
                    # survey_id = clearance_context.get('survey_id', False) or survey.id
                    request.cr.execute("UPDATE hr_employee_clearance SET is_survey=True WHERE id = " + str(employee_clearance_id))
                    request.cr.execute("UPDATE survey_user_input SET employee_id=" + str(employee_clearance_id) + " WHERE id=" + str(user_input_id))

        applicant_obj = request.env['hr.applicant']
        applicant_context = applicant_obj.context_data()
        if applicant_context:
            model = applicant_context.get('object', False)
            if model == 'hr.applicant':
                if applicant_context.get('active_ids', False):
                    applicant_id = applicant_context.get('active_ids', False)[0]
                    # survey_id = applicant_context.get('survey_id', False)  or survey.id
#                    request.cr.execute("UPDATE hr_applicant SET is_survey=True WHERE id = " + str(applicant_id))
                    request.cr.execute("UPDATE survey_user_input SET applicant_id=" + str(applicant_id) + " WHERE id=" + str(user_input_id))
        return super_res
