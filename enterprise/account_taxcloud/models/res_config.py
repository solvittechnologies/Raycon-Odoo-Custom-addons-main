# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, Warning

from taxcloud_request import TaxCloudRequest

class TaxCloudConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    taxcloud_api_id = fields.Char(string='TaxCloud API ID')
    taxcloud_api_key = fields.Char(string='TaxCloud API KEY')
    tic_category_id = fields.Many2one(related='company_id.tic_category_id', string="Default TIC Code *")

    @api.multi
    def set_default_taxcloud(self):
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param("account_taxcloud.taxcloud_api_id", (self.taxcloud_api_id or '').strip(), groups=['base.group_erp_manager'])
        Param.set_param("account_taxcloud.taxcloud_api_key", (self.taxcloud_api_key or '').strip(), groups=['base.group_erp_manager'])

    @api.model
    def get_default_taxcloud(self, fields):
        params = self.env['ir.config_parameter'].sudo()
        taxcloud_api_id = params.get_param('account_taxcloud.taxcloud_api_id', default='')
        taxcloud_api_key = params.get_param('account_taxcloud.taxcloud_api_key', default='')
        return dict(taxcloud_api_id=taxcloud_api_id, taxcloud_api_key=taxcloud_api_key)

    @api.multi
    def sync_taxcloud_category(self):
        Category = self.env['product.tic.category']
        request = TaxCloudRequest(self.taxcloud_api_id, self.taxcloud_api_key)
        res = request.get_tic_category()

        if res.get('error_message'):
            raise ValidationError(res['error_message'])

        for category in res['data']:
            if not Category.search([('code', '=', category['TICID'])], limit=1):
                Category.create({'code': category['TICID'], 'description': category['Description']})
        if not self.env.user.company_id.tic_category_id:
            self.env.user.company_id.tic_category_id = Category.search([('code', '=', 0)], limit=1)
        return True
