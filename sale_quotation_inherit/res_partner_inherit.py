from odoo import models, fields


class CompanyBranch(models.Model):
    _inherit = 'res.partner'

    branch = fields.One2many('company.branch', 'branch_id', string='Company Branches')



class CompanyBranch(models.Model):
    _name = "company.branch"
    #_inherit = 'res.partner'

    branch_id = fields.Many2one('res.partner', string='Related Company')
    name = fields.Char(string="Branch Name")

