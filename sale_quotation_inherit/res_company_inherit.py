from odoo import models, fields


class CompanyInherit(models.Model):
    _inherit = 'res.company'

    address_str1 = fields.Char(readonly=False)
    address_str2 = fields.Char(readonly=False)
    address_city = fields.Char(readonly=False)
    address_state = fields.Char(readonly=False)
    address_zip = fields.Char(readonly=False)
    address_country = fields.Char(readonly=False)

