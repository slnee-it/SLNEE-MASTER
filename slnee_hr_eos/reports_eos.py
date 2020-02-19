# -*- coding: utf-8 -*-
# Part of odoo. See LICENSE file for full copyright and licensing details.

# from odoo.report import report_sxw
from odoo import models
from datetime import datetime

# class experience_latter(report_sxw.rml_parse):

	

#     def __init__(self,cr,uid,name,context=None):
#         super(experience_latter, self).__init__(cr,uid,name,context=context)
#         self.localcontext.update({
#         	'get_islamic_date': self.get_islamic_date,
#         	})

#     def get_islamic_date(self, date):
# 	    date = str(date)
# 	    date_list = str(date).split('-')
# 	    cal = calverter.Calverter()
# 	    jd = cal.gregorian_to_jd(int(date_list[0]),int(date_list[1]),int(date_list[2]))
# 	    islamic_date = cal.jd_to_islamic(jd)
# 	    islamic_date_format = str(islamic_date[0])+"-"+str(islamic_date[1])+"-"+str(islamic_date[2])
# 	    return islamic_date_format

# class wrapped_report_experience_latter(report_sxw.rml_parse):
#     _name = 'report.hr_eos.emp_experience_letter_femaleqweb'
#     _inherit = 'report.abstract_report'
#     _template = 'hr_eos.emp_experience_letter_femaleqweb'
#     # _wrapped_report_class = experience_latter


# class wrapped_report_experience_latter_male(report_sxw.rml_parse):
#     _name = 'report.slnee_hr_eos.emp_experience_letter_maleqweb'
#     _inherit = 'report.abstract_report'
#     _template = 'slnee_hr_eos.emp_experience_letter_maleqweb'
#     # _wrapped_report_class = experience_latter