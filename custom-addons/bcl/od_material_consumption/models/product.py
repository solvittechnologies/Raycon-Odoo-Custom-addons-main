from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    analytical_account = fields.Many2one('account.analytic.account')

    def get_default_consumption_location(self):
        return self.env.ref('od_material_consumption.stock_location_material_consumption').id
    # domain = "[('usage', '=', 'inventory'), '|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]",
    consumption_location_id = fields.Many2one(
        'stock.location', "Consumption Location", company_dependent=True, check_company=True, default=get_default_consumption_location,
        help="This stock location will be used, instead of the default one, as the source location for stock moves generated when you do an inventory consumption.")