from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

class CrossoveredBudgetLinesGroup(models.Model):
    
    _name = "crossovered.budget.lines.group"
    
    name = fields.Char(string='Group Name')

class CrossoveredBudgetLines(models.Model):
    
    _inherit = "crossovered.budget.lines"
    
    group_id = fields.Many2one('crossovered.budget.lines.group', 'Group')
    

